import {
  TDFOL_ERROR_CODES,
  TDFOLFormulaError,
  TDFOLParseError,
  TdfolException,
  TdfolFormulaException,
  TdfolParseException,
  TdfolProofException,
  TdfolUnsupportedOperationException,
  isTdfolException,
  normalizeTdfolException,
} from './exceptions';

describe('TDFOL exception parity', () => {
  it('preserves browser-native Python exception hierarchy metadata', () => {
    const error = new TdfolParseException('could not parse temporal formula', {
      detail: 'unexpected quantifier',
      context: { offset: 12, token: 'forall' },
    });

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(TdfolException);
    expect(error.name).toBe('TdfolParseException');
    expect(error.code).toBe(TDFOL_ERROR_CODES.parse);
    expect(error.message).toBe('could not parse temporal formula');
    expect(error.toJSON()).toEqual({
      name: 'TdfolParseException',
      message: 'could not parse temporal formula',
      code: TDFOL_ERROR_CODES.parse,
      detail: 'unexpected quantifier',
      context: { offset: 12, token: 'forall' },
      causeName: undefined,
      causeMessage: undefined,
    });
  });

  it('normalizes unknown thrown values without Python or server fallbacks', () => {
    const normalized = normalizeTdfolException(new TypeError('bad modality'), 'proof failed');

    expect(isTdfolException(normalized)).toBe(true);
    expect(normalized.name).toBe('TdfolException');
    expect(normalized.code).toBe(TDFOL_ERROR_CODES.base);
    expect(normalized.message).toBe('proof failed');
    expect(normalized.causeName).toBe('TypeError');
    expect(normalized.causeMessage).toBe('bad modality');
  });

  it('assigns stable parity codes and Python-style aliases', () => {
    const formulaError = new TdfolFormulaException('invalid formula shape');
    const proofError = new TdfolProofException('no derivation');
    const unsupportedError = new TdfolUnsupportedOperationException('model backend unavailable');

    expect(formulaError).toBeInstanceOf(TDFOLFormulaError);
    expect(new TDFOLParseError('alias parse')).toBeInstanceOf(TdfolParseException);
    expect(formulaError.code).toBe(TDFOL_ERROR_CODES.formula);
    expect(proofError.code).toBe(TDFOL_ERROR_CODES.proof);
    expect(unsupportedError.code).toBe(TDFOL_ERROR_CODES.unsupported);
  });
});
