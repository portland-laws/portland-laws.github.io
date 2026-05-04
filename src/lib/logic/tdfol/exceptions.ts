export const TDFOL_ERROR_CODES = {
  base: 'TDFOL_ERROR',
  parse: 'TDFOL_PARSE_ERROR',
  formula: 'TDFOL_FORMULA_ERROR',
  proof: 'TDFOL_PROOF_ERROR',
  validation: 'TDFOL_VALIDATION_ERROR',
  inference: 'TDFOL_INFERENCE_ERROR',
  conversion: 'TDFOL_CONVERSION_ERROR',
  unsupported: 'TDFOL_UNSUPPORTED_OPERATION',
} as const;

export type TdfolErrorCode = (typeof TDFOL_ERROR_CODES)[keyof typeof TDFOL_ERROR_CODES];

export interface TdfolExceptionMetadata {
  readonly code: TdfolErrorCode;
  readonly detail?: string;
  readonly context?: Record<string, unknown>;
  readonly causeName?: string;
  readonly causeMessage?: string;
}

export interface TdfolExceptionPayload extends TdfolExceptionMetadata {
  readonly name: string;
  readonly message: string;
}

export interface TdfolExceptionOptions {
  readonly code?: TdfolErrorCode;
  readonly detail?: string;
  readonly context?: Record<string, unknown>;
  readonly causeName?: string;
  readonly causeMessage?: string;
}

export class TdfolException extends Error {
  public readonly code: TdfolErrorCode;
  public readonly detail?: string;
  public readonly context?: Record<string, unknown>;
  public readonly causeName?: string;
  public readonly causeMessage?: string;

  public constructor(message: string, metadata: TdfolExceptionOptions = {}) {
    super(message);
    this.name = 'TdfolException';
    this.code = metadata.code ?? TDFOL_ERROR_CODES.base;
    this.detail = metadata.detail;
    this.context = metadata.context;
    this.causeName = metadata.causeName;
    this.causeMessage = metadata.causeMessage;
    Object.setPrototypeOf(this, new.target.prototype);
  }

  public toJSON(): TdfolExceptionPayload {
    const { name, message, code, detail, context, causeName, causeMessage } = this;
    return { name, message, code, detail, context, causeName, causeMessage };
  }
}

export class TdfolParseException extends TdfolException {
  public constructor(message: string, metadata: TdfolExceptionOptions = {}) {
    super(message, { ...metadata, code: TDFOL_ERROR_CODES.parse });
    this.name = 'TdfolParseException';
  }
}
export class TdfolFormulaException extends TdfolException {
  public constructor(message: string, metadata: TdfolExceptionOptions = {}) {
    super(message, { ...metadata, code: TDFOL_ERROR_CODES.formula });
    this.name = 'TdfolFormulaException';
  }
}
export class TdfolProofException extends TdfolException {
  public constructor(message: string, metadata: TdfolExceptionOptions = {}) {
    super(message, { ...metadata, code: TDFOL_ERROR_CODES.proof });
    this.name = 'TdfolProofException';
  }
}
export class TdfolValidationException extends TdfolException {
  public constructor(message: string, metadata: TdfolExceptionOptions = {}) {
    super(message, { ...metadata, code: TDFOL_ERROR_CODES.validation });
    this.name = 'TdfolValidationException';
  }
}
export class TdfolInferenceException extends TdfolException {
  public constructor(message: string, metadata: TdfolExceptionOptions = {}) {
    super(message, { ...metadata, code: TDFOL_ERROR_CODES.inference });
    this.name = 'TdfolInferenceException';
  }
}
export class TdfolConversionException extends TdfolException {
  public constructor(message: string, metadata: TdfolExceptionOptions = {}) {
    super(message, { ...metadata, code: TDFOL_ERROR_CODES.conversion });
    this.name = 'TdfolConversionException';
  }
}
export class TdfolUnsupportedOperationException extends TdfolException {
  public constructor(message: string, metadata: TdfolExceptionOptions = {}) {
    super(message, { ...metadata, code: TDFOL_ERROR_CODES.unsupported });
    this.name = 'TdfolUnsupportedOperationException';
  }
}

export const TDFOLError = TdfolException;
export const TDFOLParseError = TdfolParseException;
export const TDFOLFormulaError = TdfolFormulaException;
export const TDFOLProofError = TdfolProofException;
export const TDFOLValidationError = TdfolValidationException;
export const TDFOLInferenceError = TdfolInferenceException;
export const TDFOLConversionError = TdfolConversionException;
export const TDFOLUnsupportedOperationError = TdfolUnsupportedOperationException;

export function isTdfolException(value: unknown): value is TdfolException {
  return value instanceof TdfolException;
}

export function normalizeTdfolException(
  value: unknown,
  fallbackMessage = 'TDFOL operation failed',
): TdfolException {
  if (isTdfolException(value)) {
    return value;
  }
  const causeName = value instanceof Error ? value.name : typeof value;
  const causeMessage = value instanceof Error ? value.message : String(value);
  return new TdfolException(fallbackMessage, { causeName, causeMessage });
}
