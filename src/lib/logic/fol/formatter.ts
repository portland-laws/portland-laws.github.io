import type { DeonticNormType } from '../deontic/parser';

export type LogicOutputFormat = 'symbolic' | 'json' | 'prolog' | 'tptp' | 'defeasible' | 'text' | 'xml';

export interface FolJsonStructure {
  quantifiers: Array<{ type: 'universal' | 'existential'; variable: string; symbol: '∀' | '∃' }>;
  predicates: Array<{ name: string; arity: number; arguments: string[] }>;
  variables: string[];
  operators: Array<{ type: string; symbol: string }>;
}

export interface LogicFormatMetadata {
  complexity: 'simple' | 'moderate' | 'complex';
  quantifier_count: number;
  predicate_count: number;
  operator_count: number;
  max_arity: number;
  [key: string]: unknown;
}

export interface FormattedFol {
  fol_formula: string;
  format: LogicOutputFormat;
  prolog_form?: string;
  tptp_form?: string;
  structured_form?: FolJsonStructure;
  metadata?: LogicFormatMetadata;
}

export interface FormattedDeontic {
  deontic_formula: string;
  norm_type: string;
  format: LogicOutputFormat;
  defeasible_form?: string;
  structured_form?: Record<string, unknown>;
  metadata?: LogicFormatMetadata;
}

export function formatFol(
  formula: string,
  outputFormat: LogicOutputFormat = 'symbolic',
  includeMetadata = true,
): FormattedFol {
  const result: FormattedFol = { fol_formula: formula, format: outputFormat };
  if (outputFormat === 'prolog') {
    result.prolog_form = convertToPrologFormat(formula);
  } else if (outputFormat === 'tptp') {
    result.tptp_form = convertToTptpFormat(formula);
  } else if (outputFormat === 'json') {
    result.structured_form = parseFolToJson(formula);
  }
  if (includeMetadata) {
    result.metadata = extractFolMetadata(formula);
  }
  return result;
}

export function formatDeontic(
  formula: string,
  normType: DeonticNormType | string,
  outputFormat: LogicOutputFormat = 'symbolic',
  includeMetadata = true,
): FormattedDeontic {
  const result: FormattedDeontic = { deontic_formula: formula, norm_type: normType, format: outputFormat };
  if (outputFormat === 'defeasible') {
    result.defeasible_form = convertToDefeasibleFormat(formula, normType);
  } else if (outputFormat === 'json') {
    result.structured_form = parseDeonticToJson(formula);
  }
  if (includeMetadata) {
    result.metadata = extractDeonticMetadata(formula, normType);
  }
  return result;
}

export function formatOutput(
  formulas: Array<Record<string, unknown>>,
  summary: Record<string, unknown>,
  outputFormat: LogicOutputFormat = 'json',
): Record<string, unknown> | string {
  if (outputFormat === 'json') {
    return {
      status: 'success',
      formulas,
      summary,
      metadata: { conversion_timestamp: getTimestamp(), tool_version: '1.0.0-ts' },
    };
  }
  if (outputFormat === 'text') {
    return formatTextOutput(formulas, summary);
  }
  if (outputFormat === 'xml') {
    return JSON.stringify({ formulas, summary });
  }
  return { error: `Unsupported output format: ${outputFormat}` };
}

export function convertToPrologFormat(folFormula: string): string {
  const universal = folFormula.match(/∀(\w+)\s*\((\w+)\((\w+)\)\s*→\s*(\w+)\((\w+)\)\)/);
  if (universal) {
    const [, variable, premise, , conclusion] = universal;
    return `${conclusion.toLowerCase()}(${variable.toUpperCase()}) :- ${premise.toLowerCase()}(${variable.toUpperCase()}).`;
  }
  const existential = folFormula.match(/∃(\w+)\s*(\w+)\((\w+)\)/);
  if (existential) {
    const [, , predicate] = existential;
    return `${predicate.toLowerCase()}(a).`;
  }
  return `% ${folFormula}`;
}

export function convertToTptpFormat(folFormula: string): string {
  const tptp = folFormula
    .replace(/∀([a-z])/g, '![$1]:')
    .replace(/∃([a-z])/g, '?[$1]:')
    .replace(/∧/g, ' & ')
    .replace(/∨/g, ' | ')
    .replace(/→/g, ' => ')
    .replace(/↔/g, ' <=> ')
    .replace(/¬/g, '~');
  return `fof(formula, axiom, ${tptp}).`;
}

export function convertToDefeasibleFormat(deonticFormula: string, normType: string): string {
  if (normType === 'obligation') {
    return `obligatory(${deonticFormula}) unless defeated.`;
  }
  if (normType === 'permission') {
    return `permitted(${deonticFormula}) unless forbidden.`;
  }
  if (normType === 'prohibition') {
    return `forbidden(${deonticFormula}) unless permitted.`;
  }
  return `norm(${deonticFormula}).`;
}

export function parseFolToJson(folFormula: string): FolJsonStructure {
  const quantifiers = [...folFormula.matchAll(/([∀∃])([a-z])/g)].map((match) => ({
    type: match[1] === '∀' ? 'universal' as const : 'existential' as const,
    variable: match[2],
    symbol: match[1] as '∀' | '∃',
  }));
  const predicates = [...folFormula.matchAll(/([A-Z][a-zA-Z]*)\(([^)]+)\)/g)].map((match) => {
    const args = match[2].split(',').map((arg) => arg.trim());
    return { name: match[1], arity: args.length, arguments: args };
  });
  const variables = [...new Set([...folFormula.matchAll(/\b([a-z])\b/g)].map((match) => match[1]))];
  const operators = [
    ...(folFormula.includes('∧') ? [{ type: 'conjunction', symbol: '∧' }] : []),
    ...(folFormula.includes('∨') ? [{ type: 'disjunction', symbol: '∨' }] : []),
    ...(folFormula.includes('→') ? [{ type: 'implication', symbol: '→' }] : []),
    ...(folFormula.includes('¬') ? [{ type: 'negation', symbol: '¬' }] : []),
  ];
  return { quantifiers, predicates, variables, operators };
}

export function parseDeonticToJson(deonticFormula: string): Record<string, unknown> {
  const deonticOperators = [...deonticFormula.matchAll(/([OPF])\(/g)].map((match) => ({
    type: { O: 'obligation', P: 'permission', F: 'prohibition' }[match[1] as 'O' | 'P' | 'F'] ?? 'unknown',
    symbol: match[1],
  }));
  const logicalPart = deonticFormula.match(/[OPF]\((.+)\)$/)?.[1] ?? '';
  return {
    deontic_operators: deonticOperators,
    predicates: parseFolToJson(deonticFormula).predicates,
    logical_structure: logicalPart ? parseFolToJson(logicalPart) : {},
  };
}

export function extractFolMetadata(formula: string): LogicFormatMetadata {
  const quantifierCount = [...formula.matchAll(/[∀∃]/g)].length;
  const predicateArgs = [...formula.matchAll(/[A-Z][a-zA-Z]*\(([^)]+)\)/g)].map((match) => match[1]);
  const operatorCount = [...formula.matchAll(/[∧∨→↔¬]/g)].length;
  const totalComplexity = quantifierCount + predicateArgs.length + operatorCount;
  return {
    complexity: totalComplexity > 10 ? 'complex' : totalComplexity > 5 ? 'moderate' : 'simple',
    quantifier_count: quantifierCount,
    predicate_count: predicateArgs.length,
    operator_count: operatorCount,
    max_arity: predicateArgs.length > 0 ? Math.max(...predicateArgs.map((args) => args.split(',').length)) : 0,
  };
}

export function extractDeonticMetadata(formula: string, normType: string): LogicFormatMetadata {
  return {
    ...extractFolMetadata(formula),
    norm_type: normType,
    deontic_operator: normType.charAt(0).toUpperCase(),
  };
}

export function getTimestamp(): string {
  return new Date().toISOString();
}

export function formatTextOutput(formulas: Array<Record<string, unknown>>, summary: Record<string, unknown>): string {
  const lines = ['Logic Conversion Results', '==============================', `Total formulas: ${formulas.length}`];
  const conversionRate = typeof summary.conversion_rate === 'number' ? summary.conversion_rate : 0;
  lines.push(`Conversion rate: ${(conversionRate * 100).toFixed(2)}%`, '');
  formulas.forEach((formula, index) => {
    lines.push(`Formula ${index + 1}:`);
    lines.push(`  Original: ${String(formula.original_text ?? '')}`);
    lines.push(`  Logic: ${String(formula.fol_formula ?? formula.deontic_formula ?? '')}`, '');
  });
  return lines.join('\n');
}
