import { LogicValidationError } from '../errors';
import type { DcecFormula } from './dcecCore';

export const DcecTemporalEvaluationOperator = {
  ALWAYS: '□',
  EVENTUALLY: '◇',
  NEXT: 'X',
  UNTIL: 'U',
  SINCE: 'S',
  YESTERDAY: 'Y',
} as const;

export type DcecTemporalEvaluationOperatorValue =
  typeof DcecTemporalEvaluationOperator[keyof typeof DcecTemporalEvaluationOperator];

export interface DcecTemporalStateMetadata {
  [key: string]: unknown;
}

export class DcecTemporalState {
  readonly time: number;
  readonly valuations: Record<string, boolean>;
  readonly metadata: DcecTemporalStateMetadata;

  constructor(time: number, valuations: Record<string, boolean> = {}, metadata: DcecTemporalStateMetadata = {}) {
    this.time = time;
    this.valuations = { ...valuations };
    this.metadata = { ...metadata };
  }

  evaluate(proposition: string): boolean {
    return this.valuations[proposition] ?? false;
  }

  toString(): string {
    return `State(t=${this.time}, ${JSON.stringify(this.valuations)})`;
  }
}

export class DcecTemporalEvaluationFormula {
  readonly operator: DcecTemporalEvaluationOperatorValue;
  readonly formula: DcecFormula;
  readonly formula2?: DcecFormula;

  constructor(
    operator: DcecTemporalEvaluationOperatorValue,
    formula: DcecFormula,
    formula2?: DcecFormula,
  ) {
    this.operator = operator;
    this.formula = formula;
    this.formula2 = formula2;
    this.validate();
  }

  evaluate(timeSequence: DcecTemporalState[], currentTime = 0): boolean {
    if (timeSequence.length === 0) {
      throw new LogicValidationError('Time sequence cannot be empty');
    }
    if (currentTime < 0 || currentTime >= timeSequence.length) {
      throw new LogicValidationError(`Invalid current_time: ${currentTime}`, { currentTime });
    }

    switch (this.operator) {
      case DcecTemporalEvaluationOperator.ALWAYS:
        return this.evaluateAlways(timeSequence, currentTime);
      case DcecTemporalEvaluationOperator.EVENTUALLY:
        return this.evaluateEventually(timeSequence, currentTime);
      case DcecTemporalEvaluationOperator.NEXT:
        return this.evaluateNext(timeSequence, currentTime);
      case DcecTemporalEvaluationOperator.UNTIL:
        return this.evaluateUntil(timeSequence, currentTime);
      case DcecTemporalEvaluationOperator.SINCE:
        return this.evaluateSince(timeSequence, currentTime);
      case DcecTemporalEvaluationOperator.YESTERDAY:
        return this.evaluateYesterday(timeSequence, currentTime);
      default:
        throw new LogicValidationError(`Unknown temporal operator: ${this.operator}`);
    }
  }

  toString(): string {
    return this.formula2 === undefined
      ? `${this.operator}(${this.formula.toString()})`
      : `(${this.formula.toString()} ${this.operator} ${this.formula2.toString()})`;
  }

  private validate() {
    const binary = this.operator === DcecTemporalEvaluationOperator.UNTIL
      || this.operator === DcecTemporalEvaluationOperator.SINCE;
    if (binary && this.formula2 === undefined) {
      throw new LogicValidationError(`Binary temporal operator ${this.operator} requires two formulas`);
    }
    if (!binary && this.formula2 !== undefined) {
      throw new LogicValidationError(`Unary temporal operator ${this.operator} takes only one formula`);
    }
  }

  private evaluateFormulaAtState(formula: DcecFormula, state: DcecTemporalState): boolean {
    let formulaString = formula.toString().trim();

    if (formulaString.startsWith('¬') || formulaString.startsWith('~')) {
      let inner = formulaString.slice(1).trim();
      inner = stripSingleOuterParens(inner);
      if (inner.endsWith('()')) inner = inner.slice(0, -2);
      return !state.evaluate(inner);
    }

    if (formulaString.endsWith('()')) formulaString = formulaString.slice(0, -2);
    return state.evaluate(formulaString);
  }

  private evaluateAlways(timeSequence: DcecTemporalState[], currentTime: number): boolean {
    for (let index = currentTime; index < timeSequence.length; index += 1) {
      if (!this.evaluateFormulaAtState(this.formula, timeSequence[index])) return false;
    }
    return true;
  }

  private evaluateEventually(timeSequence: DcecTemporalState[], currentTime: number): boolean {
    for (let index = currentTime; index < timeSequence.length; index += 1) {
      if (this.evaluateFormulaAtState(this.formula, timeSequence[index])) return true;
    }
    return false;
  }

  private evaluateNext(timeSequence: DcecTemporalState[], currentTime: number): boolean {
    const nextTime = currentTime + 1;
    if (nextTime >= timeSequence.length) return false;
    return this.evaluateFormulaAtState(this.formula, timeSequence[nextTime]);
  }

  private evaluateUntil(timeSequence: DcecTemporalState[], currentTime: number): boolean {
    const second = this.formula2!;
    for (let index = currentTime; index < timeSequence.length; index += 1) {
      if (this.evaluateFormulaAtState(second, timeSequence[index])) {
        for (let prior = currentTime; prior < index; prior += 1) {
          if (!this.evaluateFormulaAtState(this.formula, timeSequence[prior])) return false;
        }
        return true;
      }
      if (!this.evaluateFormulaAtState(this.formula, timeSequence[index])) return false;
    }
    return false;
  }

  private evaluateSince(timeSequence: DcecTemporalState[], currentTime: number): boolean {
    const second = this.formula2!;
    for (let index = currentTime; index >= 0; index -= 1) {
      if (this.evaluateFormulaAtState(second, timeSequence[index])) {
        for (let after = index + 1; after <= currentTime; after += 1) {
          if (!this.evaluateFormulaAtState(this.formula, timeSequence[after])) return false;
        }
        return true;
      }
      if (index < currentTime && !this.evaluateFormulaAtState(this.formula, timeSequence[index])) return false;
    }
    return false;
  }

  private evaluateYesterday(timeSequence: DcecTemporalState[], currentTime: number): boolean {
    if (currentTime === 0) return false;
    return this.evaluateFormulaAtState(this.formula, timeSequence[currentTime - 1]);
  }
}

export function dcecAlways(formula: DcecFormula): DcecTemporalEvaluationFormula {
  return new DcecTemporalEvaluationFormula(DcecTemporalEvaluationOperator.ALWAYS, formula);
}

export function dcecEventually(formula: DcecFormula): DcecTemporalEvaluationFormula {
  return new DcecTemporalEvaluationFormula(DcecTemporalEvaluationOperator.EVENTUALLY, formula);
}

export function dcecNext(formula: DcecFormula): DcecTemporalEvaluationFormula {
  return new DcecTemporalEvaluationFormula(DcecTemporalEvaluationOperator.NEXT, formula);
}

export function dcecUntil(formula1: DcecFormula, formula2: DcecFormula): DcecTemporalEvaluationFormula {
  return new DcecTemporalEvaluationFormula(DcecTemporalEvaluationOperator.UNTIL, formula1, formula2);
}

export function dcecSince(formula1: DcecFormula, formula2: DcecFormula): DcecTemporalEvaluationFormula {
  return new DcecTemporalEvaluationFormula(DcecTemporalEvaluationOperator.SINCE, formula1, formula2);
}

export function dcecYesterday(formula: DcecFormula): DcecTemporalEvaluationFormula {
  return new DcecTemporalEvaluationFormula(DcecTemporalEvaluationOperator.YESTERDAY, formula);
}

function stripSingleOuterParens(value: string): string {
  const trimmed = value.trim();
  return trimmed.startsWith('(') && trimmed.endsWith(')') ? trimmed.slice(1, -1).trim() : trimmed;
}
