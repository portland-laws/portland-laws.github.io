import { env, pipeline } from '@xenova/transformers';

env.allowLocalModels = false;
env.useBrowserCache = true;

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
  };
  error?: string;
}

const DEFAULT_EMBEDDING_MODEL = 'Xenova/gte-small';

let extractor: any = null;
let currentModelName = DEFAULT_EMBEDDING_MODEL;
let initializePromise: Promise<void> | null = null;

async function initialize(modelName = DEFAULT_EMBEDDING_MODEL) {
  if (extractor && currentModelName === modelName) {
    return;
  }

  if (!initializePromise) {
    initializePromise = pipeline('feature-extraction', modelName, {
      quantized: true,
    }).then((pipe) => {
      extractor = pipe;
      currentModelName = modelName;
    });
  }

  try {
    await initializePromise;
  } finally {
    initializePromise = null;
  }
}

async function embed(text: string, modelName?: string): Promise<number[]> {
  await initialize(modelName);
  const output = await extractor(text, { pooling: 'mean', normalize: true });
  const values = Array.from(output.data as Float32Array | number[]).map((value) => Number(value));
  return values;
}

self.onmessage = async (event: MessageEvent<EmbeddingRequest>) => {
  const { id, type, data } = event.data;

  try {
    if (type === 'status') {
      postResponse({ id, success: true, data: { modelName: currentModelName, isInitialized: Boolean(extractor) } });
      return;
    }

    if (type === 'embed') {
      const embedding = await embed(data.text, data.modelName);
      postResponse({ id, success: true, data: { embedding, modelName: currentModelName, isInitialized: true } });
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
