import { BoundedCache, type CacheStats } from './cache';
import { LogicConversionError, LogicValidationError } from './errors';

export type ConversionStatus = 'success' | 'partial' | 'failed' | 'cached' | 'validation_failed';

export interface ConversionMetadata {
  [key: string]: unknown;
}

export interface ConversionResultInit<Output> {
  output?: Output;
  status?: ConversionStatus;
  confidence?: number;
  errors?: string[];
  warnings?: string[];
  metadata?: ConversionMetadata;
}

export class ConversionResult<Output> {
  output?: Output;
  status: ConversionStatus;
  confidence: number;
  errors: string[];
  warnings: string[];
  metadata: ConversionMetadata;

  constructor(init: ConversionResultInit<Output> = {}) {
    this.output = init.output;
    this.status = init.status ?? 'failed';
    this.confidence = init.confidence ?? 1;
    this.errors = [...(init.errors ?? [])];
    this.warnings = [...(init.warnings ?? [])];
    this.metadata = { ...(init.metadata ?? {}) };
  }

  get success(): boolean {
    return this.status === 'success' || this.status === 'partial' || this.status === 'cached';
  }

  addError(error: string, context?: ConversionMetadata): void {
    this.errors.push(error);
    if (context) {
      const contexts = Array.isArray(this.metadata.error_contexts) ? this.metadata.error_contexts : [];
      this.metadata.error_contexts = [...contexts, context];
    }
    this.status = 'failed';
  }

  addWarning(warning: string): void {
    this.warnings.push(warning);
    if (this.status === 'success') {
      this.status = 'partial';
    }
  }

  cloneWithStatus(status: ConversionStatus): ConversionResult<Output> {
    return new ConversionResult({
      output: this.output,
      status,
      confidence: this.confidence,
      errors: this.errors,
      warnings: this.warnings,
      metadata: this.metadata,
    });
  }

  toJSON(): Record<string, unknown> {
    return {
      output: this.output === undefined ? undefined : String(this.output),
      status: this.status,
      confidence: this.confidence,
      success: this.success,
      errors: this.errors,
      warnings: this.warnings,
      metadata: this.metadata,
    };
  }
}

export class ConverterValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  metadata: ConversionMetadata;

  constructor(init: { valid?: boolean; errors?: string[]; warnings?: string[]; metadata?: ConversionMetadata } = {}) {
    this.valid = init.valid ?? true;
    this.errors = [...(init.errors ?? [])];
    this.warnings = [...(init.warnings ?? [])];
    this.metadata = { ...(init.metadata ?? {}) };
  }

  addError(error: string): void {
    this.errors.push(error);
    this.valid = false;
  }

  addWarning(warning: string): void {
    this.warnings.push(warning);
  }
}

export interface LogicConverterOptions {
  enableCaching?: boolean;
  enableValidation?: boolean;
  cacheMaxSize?: number;
  cacheTtlMs?: number;
}

export interface ConvertOptions {
  useCache?: boolean;
  confidence?: number;
  metadata?: ConversionMetadata;
  [key: string]: unknown;
}

export interface ConverterCacheStats extends CacheStats {
  cacheEnabled: boolean;
  cacheType: 'bounded';
}

export abstract class LogicConverter<Input, Output> {
  readonly enableCaching: boolean;
  readonly enableValidation: boolean;

  private readonly cache?: BoundedCache<ConversionResult<Output>>;

  constructor(options: LogicConverterOptions = {}) {
    this.enableCaching = options.enableCaching ?? true;
    this.enableValidation = options.enableValidation ?? true;
    if (this.enableCaching) {
      this.cache = new BoundedCache<ConversionResult<Output>>({
        maxSize: options.cacheMaxSize ?? 1000,
        ttlMs: options.cacheTtlMs ?? 60 * 60 * 1000,
      });
    }
  }

  abstract validateInput(input: Input): ConverterValidationResult;

  protected abstract convertImpl(input: Input, options: ConvertOptions): Output;

  convert(input: Input, options: ConvertOptions = {}): ConversionResult<Output> {
    const useCache = options.useCache ?? true;
    const cacheKey = this.generateCacheKey(input, options);

    if (this.enableCaching && useCache) {
      const cached = this.cache?.get(cacheKey);
      if (cached) {
        return cached.cloneWithStatus('cached');
      }
    }

    const result = new ConversionResult<Output>();

    try {
      if (this.enableValidation) {
        const validation = this.validateInput(input);
        if (!validation.valid) {
          return new ConversionResult({
            status: 'validation_failed',
            errors: validation.errors,
            warnings: validation.warnings,
            metadata: { validation: validation.metadata },
          });
        }
        result.warnings.push(...validation.warnings);
      }

      const startedAt = performance.now();
      const output = this.convertImpl(input, options);
      result.output = output;
      result.confidence = this.getConfidence(output, input, options);
      result.metadata = {
        ...(options.metadata ?? {}),
        ...this.getMetadata(output, input, options),
        conversion_time_ms: performance.now() - startedAt,
      };
      result.warnings.push(...this.getWarnings(output, input, options));
      result.status = result.warnings.length > 0 ? 'partial' : 'success';

      if (this.enableCaching && result.success && useCache) {
        this.cache?.set(cacheKey, result);
      }
    } catch (error) {
      if (error instanceof LogicValidationError) {
        result.status = 'validation_failed';
        result.addError(`Validation error: ${error.message}`, error.context);
      } else if (error instanceof LogicConversionError) {
        result.addError(`Conversion error: ${error.message}`, error.context);
      } else if (error instanceof Error) {
        result.addError(`Unexpected error during conversion: ${error.message}`, {
          exception_type: error.name,
        });
      } else {
        result.addError('Unexpected non-error value thrown during conversion');
      }
    }

    return result;
  }

  convertBatch(inputs: Input[], options: ConvertOptions = {}): ConversionResult<Output>[] {
    return inputs.map((input) => this.convert(input, options));
  }

  async convertAsync(input: Input, options: ConvertOptions = {}): Promise<ConversionResult<Output>> {
    return this.convert(input, options);
  }

  clearCache(): void {
    this.cache?.clear();
  }

  cleanupExpiredCache(): number {
    return this.cache?.cleanupExpired() ?? 0;
  }

  getCacheStats(): ConverterCacheStats {
    const stats =
      this.cache?.getStats() ??
      new BoundedCache<ConversionResult<Output>>({ maxSize: 0 }).getStats();
    return {
      ...stats,
      cacheEnabled: this.enableCaching,
      cacheType: 'bounded',
    };
  }

  protected getConfidence(_output: Output, _input: Input, options: ConvertOptions): number {
    return typeof options.confidence === 'number' ? options.confidence : 1;
  }

  protected getWarnings(_output: Output, _input: Input, _options: ConvertOptions): string[] {
    return [];
  }

  protected getMetadata(_output: Output, _input: Input, _options: ConvertOptions): ConversionMetadata {
    return {};
  }

  protected generateCacheKey(input: Input, options: ConvertOptions): string {
    const { useCache: _useCache, metadata: _metadata, ...cacheOptions } = options;
    return `${this.constructor.name}:${JSON.stringify(input)}:${JSON.stringify(sortObject(cacheOptions))}`;
  }
}

export class ChainedConverter<Input, Output> extends LogicConverter<Input, Output> {
  constructor(private readonly converters: Array<LogicConverter<unknown, unknown>>, options: LogicConverterOptions = {}) {
    super(options);
  }

  validateInput(input: Input): ConverterValidationResult {
    const first = this.converters[0];
    if (!first) {
      return new ConverterValidationResult({ valid: false, errors: ['No converters in chain'] });
    }
    return first.validateInput(input);
  }

  protected convertImpl(input: Input, options: ConvertOptions): Output {
    let current: unknown = input;
    for (const [index, converter] of this.converters.entries()) {
      const result = converter.convert(current, options);
      if (!result.success) {
        throw new LogicConversionError(`Conversion failed at step ${index + 1}/${this.converters.length}`, {
          step: index + 1,
          converter: converter.constructor.name,
          errors: result.errors,
        });
      }
      current = result.output;
    }
    return current as Output;
  }
}

function sortObject(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(sortObject);
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, entry]) => [key, sortObject(entry)]),
    );
  }
  return value;
}
