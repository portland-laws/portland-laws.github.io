import { normalizePredicateName } from '../normalization';
import type { NormativeElement, TemporalConstraint } from './parser';

export interface DeonticFormulaBuilderOptions {
  variable?: string;
  includeExceptions?: boolean;
  includeTemporalConstraints?: boolean;
}

export interface DeonticFormulaParts {
  operator: string;
  variable: string;
  subjectPredicate: string;
  actionPredicate: string;
  antecedents: string[];
  consequent: string;
}

export function buildDeonticFormula(
  element: NormativeElement,
  options: DeonticFormulaBuilderOptions = {},
): string {
  const parts = buildDeonticFormulaParts(element, options);
  const antecedent =
    parts.antecedents.length > 1 ? parts.antecedents.join(' ∧ ') : parts.antecedents[0];

  return `${parts.operator}(∀${parts.variable} (${antecedent} → ${parts.consequent}))`;
}

export function buildDeonticFormulaParts(
  element: NormativeElement,
  options: DeonticFormulaBuilderOptions = {},
): DeonticFormulaParts {
  const variable = normalizeVariable(options.variable ?? 'x');
  const includeExceptions = options.includeExceptions ?? true;
  const includeTemporalConstraints = options.includeTemporalConstraints ?? true;
  const subjectPredicate = toPascalPredicate(element.subjects[0] || 'Agent');
  const actionPredicate = toPascalPredicate(actionWithoutTemporal(element.actions[0] || 'Action'));
  const antecedents = [`${subjectPredicate}(${variable})`];

  for (const condition of element.conditions) {
    antecedents.push(`${toPascalPredicate(condition)}(${variable})`);
  }

  if (includeExceptions) {
    for (const exception of element.exceptions) {
      antecedents.push(`¬${toPascalPredicate(exception)}(${variable})`);
    }
  }

  if (includeTemporalConstraints) {
    for (const temporal of element.temporalConstraints) {
      antecedents.push(formatTemporalPredicate(temporal, variable));
    }
  }

  return {
    operator: element.deonticOperator,
    variable,
    subjectPredicate,
    actionPredicate,
    antecedents,
    consequent: `${actionPredicate}(${variable})`,
  };
}

export function buildDeonticAtomicPredicate(value: string, variable = 'x'): string {
  return `${toPascalPredicate(value)}(${normalizeVariable(variable)})`;
}

export function formatTemporalPredicate(constraint: TemporalConstraint, variable = 'x'): string {
  const predicate =
    constraint.type === 'deadline'
      ? 'Within'
      : constraint.type === 'duration'
        ? 'ForDuration'
        : 'Periodic';
  const valuePredicate = toPascalPredicate(constraint.value);
  return `${predicate}(${normalizeVariable(variable)}, ${valuePredicate})`;
}

function toPascalPredicate(value: string): string {
  return normalizePredicateName(value)
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('');
}

function normalizeVariable(value: string): string {
  const normalized = normalizePredicateName(value);
  return /^[a-z][A-Za-z0-9_]*$/.test(normalized) ? normalized : 'x';
}

function actionWithoutTemporal(value: string): string {
  return (
    value
      .replace(/\bwithin\s+\d+\s+(?:days?|weeks?|months?|years?)\b/gi, '')
      .replace(/\bfor\s+\d+\s+(?:days?|weeks?|months?|years?)\b/gi, '')
      .replace(/\b(?:annually|monthly|weekly|daily)\b/gi, '')
      .replace(/\s+/g, ' ')
      .trim() || 'Action'
  );
}
