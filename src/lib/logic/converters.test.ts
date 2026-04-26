import {
  ChainedConverter,
  ConversionResult,
  ConverterValidationResult,
  LogicConverter,
} from './converters';

class UppercaseConverter extends LogicConverter<string, string> {
  validateInput(input: string): ConverterValidationResult {
    const result = new ConverterValidationResult();
    if (!input.trim()) {
      result.addError('empty');
    }
    return result;
  }

  protected convertImpl(input: string): string {
    return input.toUpperCase();
  }
}

class SuffixConverter extends LogicConverter<string, string> {
  validateInput(): ConverterValidationResult {
    return new ConverterValidationResult();
  }

  protected convertImpl(input: string): string {
    return `${input}!`;
  }
}

describe('LogicConverter', () => {
  it('wraps successful conversion results and caches hits', () => {
    const converter = new UppercaseConverter();

    expect(converter.convert('hello')).toMatchObject({
      output: 'HELLO',
      status: 'success',
      success: true,
    });
    expect(converter.convert('hello')).toMatchObject({
      output: 'HELLO',
      status: 'cached',
      success: true,
    });
    expect(converter.getCacheStats()).toMatchObject({
      cacheEnabled: true,
      size: 1,
      hits: 1,
    });
  });

  it('returns validation_failed for invalid input', () => {
    expect(new UppercaseConverter().convert('   ')).toMatchObject({
      status: 'validation_failed',
      errors: ['empty'],
      success: false,
    });
  });

  it('chains converters in sequence', () => {
    const chained = new ChainedConverter<string, string>([
      new UppercaseConverter(),
      new SuffixConverter(),
    ]);

    expect(chained.convert('ok')).toMatchObject({
      output: 'OK!',
      status: 'success',
    });
  });

  it('serializes conversion results with Python-compatible fields', () => {
    const result = new ConversionResult({ output: 'P(x)', status: 'success', confidence: 0.75 });

    expect(result.toJSON()).toEqual({
      output: 'P(x)',
      status: 'success',
      confidence: 0.75,
      success: true,
      errors: [],
      warnings: [],
      metadata: {},
    });
  });
});
