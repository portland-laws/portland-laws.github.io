import { LogicParseError } from '../errors';
import { cleanDcec, createDcecWrapper, parseDcec } from './dcecWrapper';

describe('DCEC wrapper browser-native port', () => {
  it('advertises a browser-native contract without Python or server runtimes', () => {
    const capabilities = createDcecWrapper().getCapabilities();

    expect(capabilities).toEqual({
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
      filesystem: false,
      subprocess: false,
      rpc: false,
      wasmRequired: false,
      implementation: 'deterministic-typescript',
      pythonModule: 'logic/CEC/dcec_wrapper.py',
    });
  });

  it('normalizes, strips comments, and cleans DCEC expressions deterministically', () => {
    const result = parseDcec('  ((and a b))  # ignored comment ');

    expect(result.ok).toBe(true);
    expect(result.normalizedInput).toBe('((and a b)) # ignored comment');
    expect(result.cleanedDcec).toBe('(and,a,b)');
    expect(result.errors).toEqual([]);
    expect(result.metadata).toEqual({
      sourcePythonModule: 'logic/CEC/dcec_wrapper.py',
      runtime: 'browser-native-typescript',
      implementation: 'deterministic-dcec-wrapper-validation',
    });
  });

  it('supports a direct clean helper for validation pipelines', () => {
    expect(cleanDcec('B(a,b) ; comment')).toBe('(B,a,b)');
  });

  it('fails closed for invalid input instead of delegating to Python or a server', () => {
    const empty = parseDcec('   ');
    const unbalanced = parseDcec('(and a b');
    const tooLong = parseDcec('abcdef', { maxInputLength: 3 });

    expect(empty.ok).toBe(false);
    expect(empty.errors).toEqual(['Input must not be empty']);
    expect(unbalanced.ok).toBe(false);
    expect(unbalanced.errors).toEqual(['DCEC expression has unbalanced parentheses']);
    expect(tooLong.ok).toBe(false);
    expect(tooLong.errors).toEqual(['Input exceeds maximum length of 3 characters']);
  });

  it('keeps formula construction fail-closed until a native parser adapter is available', () => {
    expect(() => createDcecWrapper().parseToFormula('(and a b)')).toThrow(LogicParseError);
  });
});
