export interface CecNativeExceptionMetadata {
  readonly code: string;
  readonly detail?: string;
  readonly context?: Record<string, unknown>;
  readonly causeName?: string;
  readonly causeMessage?: string;
}

export interface CecNativeExceptionPayload extends CecNativeExceptionMetadata {
  readonly name: string;
  readonly message: string;
}

export const CEC_NATIVE_ERROR_CODES = {
  base: 'CEC_NATIVE_ERROR',
  parse: 'CEC_NATIVE_PARSE_ERROR',
  proof: 'CEC_NATIVE_PROOF_ERROR',
  validation: 'CEC_NATIVE_VALIDATION_ERROR',
  inference: 'CEC_NATIVE_INFERENCE_ERROR',
  conversion: 'CEC_NATIVE_CONVERSION_ERROR',
  unsupported: 'CEC_NATIVE_UNSUPPORTED_OPERATION',
} as const;

export type CecNativeErrorCode =
  (typeof CEC_NATIVE_ERROR_CODES)[keyof typeof CEC_NATIVE_ERROR_CODES];

export interface CecNativeExceptionOptions {
  readonly code?: CecNativeErrorCode;
  readonly detail?: string;
  readonly context?: Record<string, unknown>;
  readonly causeName?: string;
  readonly causeMessage?: string;
}

export class CecNativeException extends Error {
  public readonly code: CecNativeErrorCode;
  public readonly detail?: string;
  public readonly context?: Record<string, unknown>;
  public readonly causeName?: string;
  public readonly causeMessage?: string;

  public constructor(message: string, metadata: CecNativeExceptionOptions = {}) {
    super(message);
    this.name = 'CecNativeException';
    this.code = metadata.code ?? CEC_NATIVE_ERROR_CODES.base;
    this.detail = metadata.detail;
    this.context = metadata.context;
    this.causeName = metadata.causeName;
    this.causeMessage = metadata.causeMessage;
    Object.setPrototypeOf(this, new.target.prototype);
  }

  public toJSON(): CecNativeExceptionPayload {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      detail: this.detail,
      context: this.context,
      causeName: this.causeName,
      causeMessage: this.causeMessage,
    };
  }
}

export class CecNativeParseException extends CecNativeException {
  public constructor(message: string, metadata: CecNativeExceptionOptions = {}) {
    super(message, { ...metadata, code: CEC_NATIVE_ERROR_CODES.parse });
    this.name = 'CecNativeParseException';
  }
}

export class CecNativeProofException extends CecNativeException {
  public constructor(message: string, metadata: CecNativeExceptionOptions = {}) {
    super(message, { ...metadata, code: CEC_NATIVE_ERROR_CODES.proof });
    this.name = 'CecNativeProofException';
  }
}

export class CecNativeValidationException extends CecNativeException {
  public constructor(message: string, metadata: CecNativeExceptionOptions = {}) {
    super(message, { ...metadata, code: CEC_NATIVE_ERROR_CODES.validation });
    this.name = 'CecNativeValidationException';
  }
}

export class CecNativeInferenceException extends CecNativeException {
  public constructor(message: string, metadata: CecNativeExceptionOptions = {}) {
    super(message, { ...metadata, code: CEC_NATIVE_ERROR_CODES.inference });
    this.name = 'CecNativeInferenceException';
  }
}

export class CecNativeConversionException extends CecNativeException {
  public constructor(message: string, metadata: CecNativeExceptionOptions = {}) {
    super(message, { ...metadata, code: CEC_NATIVE_ERROR_CODES.conversion });
    this.name = 'CecNativeConversionException';
  }
}

export class CecNativeUnsupportedOperationException extends CecNativeException {
  public constructor(message: string, metadata: CecNativeExceptionOptions = {}) {
    super(message, { ...metadata, code: CEC_NATIVE_ERROR_CODES.unsupported });
    this.name = 'CecNativeUnsupportedOperationException';
  }
}

export const CECNativeError = CecNativeException;
export const CECNativeParseError = CecNativeParseException;
export const CECNativeProofError = CecNativeProofException;
export const CECNativeValidationError = CecNativeValidationException;
export const CECNativeInferenceError = CecNativeInferenceException;
export const CECNativeConversionError = CecNativeConversionException;
export const CECNativeUnsupportedOperationError = CecNativeUnsupportedOperationException;

export function isCecNativeException(value: unknown): value is CecNativeException {
  return value instanceof CecNativeException;
}

export function normalizeCecNativeException(
  value: unknown,
  fallbackMessage = 'CEC native operation failed',
): CecNativeException {
  if (isCecNativeException(value)) {
    return value;
  }

  if (value instanceof Error) {
    return new CecNativeException(fallbackMessage, {
      causeName: value.name,
      causeMessage: value.message,
    });
  }

  return new CecNativeException(fallbackMessage, {
    causeName: typeof value,
    causeMessage: String(value),
  });
}
