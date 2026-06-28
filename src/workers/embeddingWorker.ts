type EmbeddingRequest =
  | {
      id: string;
      type: 'embed';
      data: { text: string; modelName?: string };
    }
  | {
      id: string;
      type: 'status';
      data?: Record<string, never>;
    };

interface EmbeddingResponse {
  id: string;
  success: boolean;
  data?: {
    embedding?: number[];
    modelName?: string;
    isInitialized?: boolean;
    attemptedModels?: string[];
    failedAttempts?: string[];
  };
  error?: string;
}

interface EmbeddingAttempt {
  key: string;
  modelName: string;
  options: Record<string, string>;
}

interface EmbedResult {
  embedding: number[];
  modelName: string;
  attemptedModels: string[];
}

const DEFAULT_EMBEDDING_MODEL =
  readEnvString('VITE_DEFAULT_EMBEDDING_MODEL') || 'Xenova/gte-small';
const FALLBACK_EMBEDDING_MODELS = parseModelList(
  readEnvString('VITE_EMBEDDING_MODEL_FALLBACKS') || '',
);
const DEFAULT_EMBEDDING_DTYPE = readEnvString('VITE_EMBEDDING_DTYPE') || 'fp32';
const DEFAULT_EMBEDDING_DEVICE = readEnvString('VITE_EMBEDDING_DEVICE');

let extractor: any = null;
let currentModelName = DEFAULT_EMBEDDING_MODEL;
let currentExtractorKey: string | null = null;
let initializePromise: Promise<void> | null = null;
let initializeTargetKey: string | null = null;
let transformersPromise: Promise<{ pipeline: any; env: any }> | null = null;
const failedAttempts = new Set<string>();

async function getTransformers() {
  if (!transformersPromise) {
    transformersPromise = (async () => {
      const transformers = await import('@huggingface/transformers');
      transformers.env.allowLocalModels = false;
      transformers.env.useBrowserCache = true;
      return { pipeline: transformers.pipeline, env: transformers.env };
    })();
  }
  return transformersPromise;
}

async function initialize(attempt: EmbeddingAttempt) {
  if (extractor && currentExtractorKey === attempt.key) {
    return;
  }

  if (initializePromise && initializeTargetKey === attempt.key) {
    await initializePromise;
    return;
  }

  initializeTargetKey = attempt.key;
  initializePromise = getTransformers()
    .then(({ pipeline }) => pipeline('feature-extraction', attempt.modelName, attempt.options))
    .then(async (pipe: any) => {
      await disposeExtractor();
      extractor = pipe;
      currentModelName = attempt.modelName;
      currentExtractorKey = attempt.key;
    });

  try {
    await initializePromise;
  } finally {
    if (initializeTargetKey === attempt.key) {
      initializePromise = null;
      initializeTargetKey = null;
    }
  }
}

async function disposeExtractor(key = currentExtractorKey) {
  if (!extractor || (key && currentExtractorKey !== key)) {
    return;
  }

  const previousExtractor = extractor;
  extractor = null;
  currentExtractorKey = null;

  if (typeof previousExtractor.dispose === 'function') {
    await previousExtractor.dispose();
  }
}

async function embed(text: string, modelName?: string): Promise<EmbedResult> {
  const normalizedText = text.trim();
  if (!normalizedText) {
    throw new Error('Cannot generate an embedding for empty text');
  }

  const attempts = getEmbeddingAttempts(modelName);
  const errors: string[] = [];
  const attemptedModels: string[] = [];

  for (const attempt of attempts) {
    if (failedAttempts.has(attempt.key) && attempts.some((candidate) => !failedAttempts.has(candidate.key))) {
      continue;
    }

    attemptedModels.push(describeAttempt(attempt));

    try {
      await initialize(attempt);
      const output = await extractor(normalizedText, { pooling: 'mean', normalize: true });
      const embedding = extractEmbeddingVector(output);

      return {
        embedding,
        modelName: attempt.modelName,
        attemptedModels,
      };
    } catch (error) {
      failedAttempts.add(attempt.key);
      errors.push(`${describeAttempt(attempt)}: ${formatError(error)}`);
      await disposeExtractor(attempt.key);
    }
  }

  throw new Error(`Embedding model execution failed: ${errors.join(' | ')}`);
}

self.onmessage = async (event: MessageEvent<EmbeddingRequest>) => {
  const { id, type, data } = event.data;

  try {
    if (type === 'status') {
      postResponse({
        id,
        success: true,
        data: {
          modelName: currentModelName,
          isInitialized: Boolean(extractor),
          failedAttempts: Array.from(failedAttempts),
        },
      });
      return;
    }

    if (type === 'embed') {
      const result = await embed(data.text, data.modelName);
      postResponse({
        id,
        success: true,
        data: {
          embedding: result.embedding,
          modelName: result.modelName,
          isInitialized: true,
          attemptedModels: result.attemptedModels,
          failedAttempts: Array.from(failedAttempts),
        },
      });
      return;
    }

    throw new Error(`Unknown embedding worker request: ${type}`);
  } catch (error) {
    postResponse({
      id,
      success: false,
      error: error instanceof Error ? error.message : 'Embedding worker failed',
    });
  }
};

function postResponse(response: EmbeddingResponse) {
  self.postMessage(response);
}

function readEnvString(key: string): string | undefined {
  const value = import.meta.env[key];
  if (typeof value !== 'string') {
    return undefined;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

function parseModelList(value: string) {
  return value
    .split(',')
    .map((modelName) => modelName.trim())
    .filter(Boolean);
}

function getEmbeddingAttempts(modelName?: string): EmbeddingAttempt[] {
  const models = uniqueStrings([
    modelName,
    DEFAULT_EMBEDDING_MODEL,
    ...FALLBACK_EMBEDDING_MODELS,
  ].filter((candidate): candidate is string => Boolean(candidate)));
  const optionVariants = getPipelineOptionVariants();

  return models.flatMap((candidateModel) => optionVariants.map((options) => ({
    key: `${candidateModel}:${JSON.stringify(options)}`,
    modelName: candidateModel,
    options,
  })));
}

function getPipelineOptionVariants() {
  const baseOptions: Record<string, string> = {};
  if (DEFAULT_EMBEDDING_DTYPE && DEFAULT_EMBEDDING_DTYPE !== 'auto') {
    baseOptions.dtype = DEFAULT_EMBEDDING_DTYPE;
  }
  if (DEFAULT_EMBEDDING_DEVICE) {
    baseOptions.device = DEFAULT_EMBEDDING_DEVICE;
  }

  const variants = [baseOptions];
  if (baseOptions.dtype) {
    const fallbackOptions = { ...baseOptions };
    delete fallbackOptions.dtype;
    variants.push(fallbackOptions);
  }

  return dedupeOptionVariants(variants);
}

function dedupeOptionVariants(variants: Array<Record<string, string>>) {
  const seen = new Set<string>();
  return variants.filter((variant) => {
    const key = JSON.stringify(variant);
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function uniqueStrings(values: string[]) {
  return values.filter((value, index) => values.indexOf(value) === index);
}

function extractEmbeddingVector(output: any): number[] {
  const directValues = flattenNumericValues(output?.data ?? output);
  const values = directValues.length > 0 || typeof output?.tolist !== 'function'
    ? directValues
    : flattenNumericValues(output.tolist());

  if (values.length === 0) {
    throw new Error('Embedding model returned an empty vector');
  }

  const invalidIndex = values.findIndex((value) => !Number.isFinite(value));
  if (invalidIndex !== -1) {
    throw new Error(`Embedding model returned a non-finite value at index ${invalidIndex}`);
  }

  return values;
}

function flattenNumericValues(value: unknown): number[] {
  if (value == null) {
    return [];
  }

  if (ArrayBuffer.isView(value) && !(value instanceof DataView)) {
    return Array.from(value as unknown as ArrayLike<number | bigint>, (item) => Number(item));
  }

  if (Array.isArray(value)) {
    return value.flatMap((item) => {
      if (typeof item === 'number' || typeof item === 'bigint') {
        return [Number(item)];
      }
      return flattenNumericValues(item);
    });
  }

  if (typeof value === 'object' && 'data' in value) {
    return flattenNumericValues((value as { data?: unknown }).data);
  }

  return [];
}

function describeAttempt(attempt: EmbeddingAttempt) {
  const optionDescription = Object.keys(attempt.options).length > 0
    ? Object.entries(attempt.options).map(([key, value]) => `${key}=${value}`).join(',')
    : 'default';
  return `${attempt.modelName} (${optionDescription})`;
}

function formatError(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}
