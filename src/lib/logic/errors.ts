export interface LogicErrorContext {
  [key: string]: unknown;
}

export class LogicError extends Error {
  readonly context: LogicErrorContext;

  constructor(message: string, context: LogicErrorContext = {}) {
    super(message);
    this.name = new.target.name;
    this.context = context;
  }

  override toString(): string {
    const contextEntries = Object.entries(this.context);
    if (contextEntries.length === 0) {
      return this.message;
    }
    const context = contextEntries.map(([key, value]) => `${key}=${String(value)}`).join(', ');
    return `${this.message} (Context: ${context})`;
  }
}

export class LogicConversionError extends LogicError {}
export class LogicValidationError extends LogicError {}
export class LogicParseError extends LogicError {}
export class LogicProofError extends LogicError {}
export class LogicTranslationError extends LogicError {}
export class LogicBridgeError extends LogicError {}
export class LogicConfigurationError extends LogicError {}
export class DeonticLogicError extends LogicError {}
export class ModalLogicError extends LogicError {}
export class TemporalLogicError extends LogicError {}

