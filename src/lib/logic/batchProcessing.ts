import { FOLConverter, type FolConverterOptions, type FolFormula } from './fol/converter';
import { BrowserNativeLogicBridge, type BridgeProofRequest } from './integration/bridge';
import type { ConversionResult } from './converters';
import type { ProofResult } from './types';

export interface BatchError {
  index?: number;
  error: string;
}

export interface BatchResultInit<Result> {
  totalItems: number;
  successful: number;
  failed: number;
  totalTime: number;
  itemsPerSecond: number;
  results?: Result[];
  errors?: BatchError[];
}

export class BatchResult<Result = unknown> {
  readonly totalItems: number;
  readonly successful: number;
  readonly failed: number;
  readonly totalTime: number;
  readonly itemsPerSecond: number;
  readonly results: Result[];
  readonly errors: BatchError[];

  constructor(init: BatchResultInit<Result>) {
    this.totalItems = init.totalItems;
    this.successful = init.successful;
    this.failed = init.failed;
    this.totalTime = init.totalTime;
    this.itemsPerSecond = init.itemsPerSecond;
    this.results = [...(init.results ?? [])];
    this.errors = [...(init.errors ?? [])];
  }

  successRate(): number {
    return this.totalItems === 0 ? 0 : (this.successful / this.totalItems) * 100;
  }

  toDict(): Record<string, unknown> {
    return {
      total_items: this.totalItems,
      successful: this.successful,
      failed: this.failed,
      total_time: this.totalTime,
      items_per_second: this.itemsPerSecond,
      success_rate: this.successRate(),
      results_count: this.results.length,
      errors_count: this.errors.length,
    };
  }

  toJson(indent = 2): string {
    return JSON.stringify(this.toDict(), null, indent);
  }

  toCsv(): string {
    return batchResultToCsv(this);
  }
}

export type BatchResultExportFormat = 'dict' | 'json' | 'csv';

export interface BatchResultExportOptions {
  jsonIndent?: number;
}

export function exportBatchResult<Result>(
  result: BatchResult<Result>,
  format: BatchResultExportFormat,
  options: BatchResultExportOptions = {},
): Record<string, unknown> | string {
  if (format === 'dict') return result.toDict();
  if (format === 'json') return result.toJson(options.jsonIndent);
  return result.toCsv();
}

export function batchResultToCsv<Result>(result: BatchResult<Result>): string {
  const dict = result.toDict();
  const rows = [['metric', 'value']];
  for (const [metric, value] of Object.entries(dict)) {
    rows.push([metric, String(value)]);
  }
  return rows.map((row) => row.map(escapeCsvCell).join(',')).join('\n');
}

function escapeCsvCell(value: string): string {
  if (!/[",\n\r]/.test(value)) return value;
  return `"${value.replace(/"/g, '""')}"`;
}

export interface BatchProcessorOptions {
  maxConcurrency?: number;
  useProcessPool?: boolean;
  showProgress?: boolean;
  now?: () => number;
  onProgress?: (event: BatchProgressEvent) => void;
}

export interface BatchProgressEvent {
  index: number;
  total: number;
  phase: 'start' | 'success' | 'error' | 'complete';
}

export type BatchProcessFunction<Item, Result> = (
  item: Item,
  index: number,
) => Result | Promise<Result>;

export class BatchProcessor {
  readonly maxConcurrency: number;
  readonly useProcessPool: boolean;
  readonly showProgress: boolean;

  private readonly now: () => number;
  private readonly onProgress?: (event: BatchProgressEvent) => void;

  constructor(options: BatchProcessorOptions = {}) {
    this.maxConcurrency = Math.max(1, Math.trunc(options.maxConcurrency ?? 10));
    this.useProcessPool = options.useProcessPool ?? false;
    this.showProgress = options.showProgress ?? true;
    this.now = options.now ?? (() => performance.now() / 1000);
    this.onProgress = options.onProgress;
  }

  async processBatchAsync<Item, Result>(
    items: Item[],
    processFunc: BatchProcessFunction<Item, Result>,
  ): Promise<BatchResult<Result>> {
    const startTime = this.now();
    const settled = await this.mapWithConcurrency(items, processFunc);
    return this.collectResults(items.length, settled, startTime);
  }

  async processBatchParallel<Item, Result>(
    items: Item[],
    processFunc: BatchProcessFunction<Item, Result>,
  ): Promise<BatchResult<Result>> {
    return this.processBatchAsync(items, processFunc);
  }

  private async mapWithConcurrency<Item, Result>(
    items: Item[],
    processFunc: BatchProcessFunction<Item, Result>,
  ): Promise<
    Array<
      | { success: true; result: Result; index: number }
      | { success: false; error: string; index: number }
    >
  > {
    const outputs = new Array<
      | { success: true; result: Result; index: number }
      | { success: false; error: string; index: number }
    >(items.length);
    let nextIndex = 0;

    const workerCount = Math.min(this.maxConcurrency, items.length);
    const workers = Array.from({ length: workerCount }, async () => {
      while (nextIndex < items.length) {
        const index = nextIndex;
        nextIndex += 1;
        if (this.showProgress) this.onProgress?.({ index, total: items.length, phase: 'start' });
        try {
          outputs[index] = {
            success: true,
            result: await processFunc(items[index], index),
            index,
          };
          if (this.showProgress)
            this.onProgress?.({ index, total: items.length, phase: 'success' });
        } catch (error) {
          outputs[index] = {
            success: false,
            error: error instanceof Error ? error.message : String(error),
            index,
          };
          if (this.showProgress) this.onProgress?.({ index, total: items.length, phase: 'error' });
        }
      }
    });

    await Promise.all(workers);
    if (this.showProgress)
      this.onProgress?.({ index: items.length, total: items.length, phase: 'complete' });
    return outputs;
  }

  private collectResults<Result>(
    totalItems: number,
    settled: Array<
      | { success: true; result: Result; index: number }
      | { success: false; error: string; index: number }
    >,
    startTime: number,
  ): BatchResult<Result> {
    const results: Result[] = [];
    const errors: BatchError[] = [];
    let successful = 0;
    let failed = 0;

    for (const itemResult of settled) {
      if (itemResult.success) {
        successful += 1;
        results.push(itemResult.result);
      } else {
        failed += 1;
        errors.push({ index: itemResult.index, error: itemResult.error });
      }
    }

    const totalTime = Math.max(0, this.now() - startTime);
    return new BatchResult({
      totalItems,
      successful,
      failed,
      totalTime,
      itemsPerSecond: totalTime > 0 ? totalItems / totalTime : 0,
      results,
      errors,
    });
  }
}

export class FOLBatchProcessor {
  private readonly processor: BatchProcessor;
  private readonly converterOptions: FolConverterOptions;

  constructor(maxConcurrency = 10, converterOptions: FolConverterOptions = {}) {
    this.processor = new BatchProcessor({ maxConcurrency });
    this.converterOptions = converterOptions;
  }

  async convertBatch(
    texts: string[],
    options: { useNlp?: boolean; confidenceThreshold?: number } = {},
  ): Promise<BatchResult<ConversionResult<FolFormula>>> {
    const converter = new FOLConverter({
      ...this.converterOptions,
      useNlp: options.useNlp ?? this.converterOptions.useNlp,
      confidenceThreshold: options.confidenceThreshold ?? this.converterOptions.confidenceThreshold,
    });
    return this.processor.processBatchAsync(texts, async (text) => converter.convertAsync(text));
  }
}

export class ProofBatchProcessor {
  private readonly processor: BatchProcessor;
  private readonly bridge: BrowserNativeLogicBridge;

  constructor(maxConcurrency = 5, bridge = new BrowserNativeLogicBridge()) {
    this.processor = new BatchProcessor({ maxConcurrency });
    this.bridge = bridge;
  }

  async proveBatch(
    formulas: Array<string | BridgeProofRequest>,
    prover = 'tdfol',
    useCache = true,
  ): Promise<BatchResult<ProofResult>> {
    return this.processor.processBatchAsync(formulas, async (formula) => {
      const request =
        typeof formula === 'string'
          ? { logic: normalizeProofLogic(prover), theorem: formula, axioms: [formula] }
          : formula;
      const result = this.bridge.prove(request);
      return {
        ...result,
        method: `${result.method ?? 'bridge-proof'}${useCache ? ':cache-eligible' : ''}`,
      };
    });
  }
}

export interface ChunkedBatchProcessorOptions {
  chunkSize?: number;
  maxConcurrency?: number;
  now?: () => number;
  onChunkStart?: (chunkIndex: number, totalChunks: number) => void;
}

export class ChunkedBatchProcessor {
  readonly chunkSize: number;
  private readonly processor: BatchProcessor;
  private readonly now: () => number;
  private readonly onChunkStart?: (chunkIndex: number, totalChunks: number) => void;

  constructor(options: ChunkedBatchProcessorOptions = {}) {
    this.chunkSize = Math.max(1, Math.trunc(options.chunkSize ?? 100));
    this.processor = new BatchProcessor({
      maxConcurrency: options.maxConcurrency ?? 10,
      now: options.now,
    });
    this.now = options.now ?? (() => performance.now() / 1000);
    this.onChunkStart = options.onChunkStart;
  }

  async processLargeBatch<Item, Result>(
    items: Item[],
    processFunc: BatchProcessFunction<Item, Result>,
  ): Promise<BatchResult<Result>> {
    const startTime = this.now();
    const totalResults: Result[] = [];
    const totalErrors: BatchError[] = [];
    let successful = 0;
    let failed = 0;
    const totalChunks = Math.ceil(items.length / this.chunkSize);

    for (let offset = 0; offset < items.length; offset += this.chunkSize) {
      const chunk = items.slice(offset, offset + this.chunkSize);
      const chunkIndex = Math.floor(offset / this.chunkSize);
      this.onChunkStart?.(chunkIndex + 1, totalChunks);
      const chunkResult = await this.processor.processBatchAsync(chunk, (item, index) =>
        processFunc(item, offset + index),
      );
      totalResults.push(...chunkResult.results);
      totalErrors.push(
        ...chunkResult.errors.map((error) => ({
          ...error,
          index: error.index === undefined ? undefined : error.index + offset,
        })),
      );
      successful += chunkResult.successful;
      failed += chunkResult.failed;
    }

    const totalTime = Math.max(0, this.now() - startTime);
    return new BatchResult({
      totalItems: items.length,
      successful,
      failed,
      totalTime,
      itemsPerSecond: totalTime > 0 ? items.length / totalTime : 0,
      results: totalResults,
      errors: totalErrors,
    });
  }
}

export function normalizeProofLogic(prover: string): BridgeProofRequest['logic'] {
  const normalized = prover.toLowerCase();
  if (normalized === 'cec' || normalized === 'dcec' || normalized === 'tdfol') return normalized;
  return 'tdfol';
}
