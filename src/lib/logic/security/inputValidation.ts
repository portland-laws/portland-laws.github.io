import { LogicValidationError } from '../errors';

export const MAX_TEXT_LENGTH = 10000;

export function validateText(text: unknown, options: { maxLength?: number } = {}): asserts text is string {
  const maxLength = options.maxLength ?? MAX_TEXT_LENGTH;
  if (typeof text !== 'string') {
    throw new LogicValidationError(`'text' must be a string, got ${typeof text}`, {
      field: 'text',
      type: typeof text,
    });
  }
  if (!text.trim()) {
    throw new LogicValidationError("'text' must not be empty.", { field: 'text' });
  }
  if (text.length > maxLength) {
    throw new LogicValidationError(`'text' exceeds maximum length of ${maxLength} characters (got ${text.length}).`, {
      field: 'text',
      length: text.length,
      max: maxLength,
    });
  }
}

export function validateFormula(formula: unknown): asserts formula is string {
  validateFormulaString(formula, 'formula');
}

export function validateFormulaList(formulas: unknown): string[] {
  if (!isIterable(formulas) || typeof formulas === 'string') {
    throw new LogicValidationError(`'formulas' must be iterable, got ${typeof formulas}`, {
      field: 'formulas',
      type: typeof formulas,
    });
  }
  const values = [...formulas] as unknown[];
  values.forEach((formula, index) => validateFormulaString(formula, `formulas[${index}]`));
  return values as string[];
}

export class InputValidator {
  validateText(text: unknown, options: { maxLength?: number } = {}): string {
    validateText(text, options);
    return text;
  }

  validateFormula(formula: unknown): string {
    validateFormula(formula);
    return formula;
  }

  validateFormulaList(formulas: unknown): string[] {
    return validateFormulaList(formulas);
  }
}

function validateFormulaString(formula: unknown, fieldName: string): asserts formula is string {
  if (typeof formula !== 'string') {
    throw new LogicValidationError(`'${fieldName}' must be a string, got ${typeof formula}`, {
      field: fieldName,
      type: typeof formula,
    });
  }
  if (!formula.trim()) {
    throw new LogicValidationError(`'${fieldName}' must not be empty.`, { field: fieldName });
  }
  if (formula.includes('\0')) {
    throw new LogicValidationError(`'${fieldName}' contains null bytes.`, { field: fieldName });
  }
}

function isIterable(value: unknown): value is Iterable<unknown> {
  return Boolean(value && typeof (value as Iterable<unknown>)[Symbol.iterator] === 'function');
}
