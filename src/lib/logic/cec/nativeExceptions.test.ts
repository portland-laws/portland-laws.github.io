import {
  CEC_NATIVE_ERROR_CODES,
  CecNativeException,
  CecNativeParseException,
  CecNativeProofException,
  CecNativeUnsupportedOperationException,
  isCecNativeException,
  normalizeCecNativeException,
} from './nativeExceptions';

describe('CEC native exception parity', () => {
  it('preserves browser-native Python exception hierarchy metadata', () => {
    const error = new CecNativeParseException('could not parse rule', {
      detail: 'unexpected token',
      context: { line: 3, token: ']' },
    });

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(CecNativeException);
    expect(error.name).toBe('CecNativeParseException');
    expect(error.code).toBe(CEC_NATIVE_ERROR_CODES.parse);
    expect(error.message).toBe('could not parse rule');
    expect(error.toJSON()).toEqual({
      name: 'CecNativeParseException',
      message: 'could not parse rule',
      code: CEC_NATIVE_ERROR_CODES.parse,
      detail: 'unexpected token',
      context: { line: 3, token: ']' },
      causeName: undefined,
      causeMessage: undefined,
    });
  });

  it('normalizes unknown thrown values without Python or server fallbacks', () => {
    const normalized = normalizeCecNativeException(new TypeError('bad arity'), 'proof failed');

    expect(isCecNativeException(normalized)).toBe(true);
    expect(normalized.name).toBe('CecNativeException');
    expect(normalized.code).toBe(CEC_NATIVE_ERROR_CODES.base);
    expect(normalized.message).toBe('proof failed');
    expect(normalized.causeName).toBe('TypeError');
    expect(normalized.causeMessage).toBe('bad arity');
  });

  it('assigns stable parity codes for proof and unsupported-operation errors', () => {
    const proofError = new CecNativeProofException('no derivation');
    const unsupportedError = new CecNativeUnsupportedOperationException(
      'quantifier mode unavailable',
    );

    expect(proofError.code).toBe(CEC_NATIVE_ERROR_CODES.proof);
    expect(unsupportedError.code).toBe(CEC_NATIVE_ERROR_CODES.unsupported);
  });
});
