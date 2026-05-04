import {
  atom,
  box,
  checkModalTableaux,
  diamond,
  not,
  type ModalFormula,
} from '../../modalTableaux';

export type ModalExtensionOutputFormat = 'formula' | 'json' | 'prolog' | 'tptp';
export type ModalExtensionOperator = 'necessary' | 'possible';
export type ModalExtensionOptions = {
  outputFormat?: ModalExtensionOutputFormat;
  runTableaux?: boolean;
};
export type ModalExtensionConversionOptions = ModalExtensionOptions & { context?: string };
export type ModalExtensionClause = {
  id: number;
  text: string;
  subject: string;
  action: string;
  operator: ModalExtensionOperator;
  negated: boolean;
  formula: string;
};

export const MODAL_LOGIC_EXTENSION_METADATA = {
  sourcePythonModule: 'logic/integration/converters/modal_logic_extension.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  failClosed: true,
  parity: [
    'modal_operator_extraction',
    'necessity_possibility_projection',
    'local_tableaux_validation',
    'python_style_facade_aliases',
  ],
} as const;

const SENTENCE_SPLIT = /[.!?;]+/u;
const NECESSITY_RE = /\b(must|shall|required to|has to|have to|needs to|is obligated to)\b/iu;
const POSSIBILITY_RE = /\b(may|can|could|is permitted to|is allowed to|has permission to)\b/iu;
const PROHIBITION_RE =
  /\b(must not|shall not|may not|cannot|can't|is prohibited from|is forbidden from)\b/iu;

export class BrowserNativeModalLogicExtension {
  readonly metadata = MODAL_LOGIC_EXTENSION_METADATA;
  private readonly outputFormat: ModalExtensionOutputFormat;
  private readonly runTableaux: boolean;

  constructor(options: ModalExtensionOptions = {}) {
    this.outputFormat = options.outputFormat ?? 'formula';
    this.runTableaux = options.runTableaux ?? false;
  }

  convert(text: string, options: ModalExtensionConversionOptions = {}) {
    const outputFormat = options.outputFormat ?? this.outputFormat;
    const sourceText = text.trim();
    if (sourceText.length < 4)
      return failModalExtension(
        text,
        outputFormat,
        'Text must contain at least one modal statement.',
      );

    const clauses = extractClauses(sourceText);
    if (clauses.length === 0)
      return failModalExtension(
        text,
        outputFormat,
        'No necessity or possibility modal operator found.',
      );

    const tableaux =
      (options.runTableaux ?? this.runTableaux)
        ? checkModalTableaux(combineModalFormulas(clauses))
        : null;
    return {
      status: 'success' as const,
      success: true,
      sourceText: text,
      outputFormat,
      output: formatModalOutput(clauses, outputFormat),
      formulas: clauses.map((clause) => clause.formula),
      clauses,
      tableaux,
      warnings: [],
      errors: [],
      metadata: {
        ...MODAL_LOGIC_EXTENSION_METADATA,
        clause_count: clauses.length,
        output_format: outputFormat,
        tableaux_checked: tableaux !== null,
        context: options.context ?? null,
      },
    };
  }

  convertBatch(texts: string[], options: ModalExtensionConversionOptions = {}) {
    return texts.map((text) => this.convert(text, options));
  }
}

export function createBrowserNativeModalLogicExtension(options: ModalExtensionOptions = {}) {
  return new BrowserNativeModalLogicExtension(options);
}

export const create_modal_logic_extension = createBrowserNativeModalLogicExtension;

export function convertModalLogicExtension(
  text: string,
  options: ModalExtensionConversionOptions = {},
) {
  return new BrowserNativeModalLogicExtension(options).convert(text, options);
}

export const convert_modal_logic_extension = convertModalLogicExtension;

function extractClauses(text: string): ModalExtensionClause[] {
  return text
    .split(SENTENCE_SPLIT)
    .map((part) => part.trim())
    .filter((part) => part.length > 0)
    .map(parseClause)
    .filter((clause): clause is Omit<ModalExtensionClause, 'id'> => clause !== null)
    .map((clause, index) => ({ ...clause, id: index + 1 }));
}

function parseClause(text: string): Omit<ModalExtensionClause, 'id'> | null {
  const prohibition = PROHIBITION_RE.exec(text);
  const possibility = prohibition ? null : POSSIBILITY_RE.exec(text);
  const match = prohibition ?? NECESSITY_RE.exec(text) ?? possibility;
  if (!match || match.index <= 0) return null;

  const subject = cleanAtom(text.slice(0, match.index));
  const action = cleanAtom(text.slice(match.index + match[0].length));
  if (!subject || !action) return null;

  const operator: ModalExtensionOperator = possibility ? 'possible' : 'necessary';
  const negated = prohibition !== null;
  const name = `${toPascal(subject)}_${toPascal(action)}`;
  return {
    text,
    subject,
    action,
    operator,
    negated,
    formula: `${operator === 'necessary' ? 'box' : 'diamond'}(${negated ? `not(${name})` : name})`,
  };
}

function combineModalFormulas(clauses: ModalExtensionClause[]): ModalFormula {
  const formulas = clauses.map((clause) => {
    const base = atom(`${toPascal(clause.subject)}_${toPascal(clause.action)}`);
    return clause.operator === 'necessary' ? box(clause.negated ? not(base) : base) : diamond(base);
  });
  return formulas.length === 1 ? formulas[0] : { kind: 'and', formulas };
}

function formatModalOutput(
  clauses: ModalExtensionClause[],
  outputFormat: ModalExtensionOutputFormat,
) {
  if (outputFormat === 'json')
    return { clauses, formulas: clauses.map((clause) => clause.formula) };
  if (outputFormat === 'prolog')
    return clauses
      .map((clause) => `modal_clause(${clause.id}, ${JSON.stringify(clause.formula)}).`)
      .join('\n');
  if (outputFormat === 'tptp')
    return clauses
      .map((clause) => `fof(modal_clause_${clause.id}, axiom, ${JSON.stringify(clause.formula)}).`)
      .join('\n');
  return clauses.map((clause) => clause.formula).join('\n');
}

function failModalExtension(text: string, outputFormat: ModalExtensionOutputFormat, error: string) {
  return {
    status: 'validation_failed' as const,
    success: false,
    sourceText: text,
    outputFormat,
    output: '',
    formulas: [],
    clauses: [],
    tableaux: null,
    warnings: [],
    errors: [error],
    metadata: { ...MODAL_LOGIC_EXTENSION_METADATA, output_format: outputFormat },
  };
}

function cleanAtom(value: string): string {
  return value
    .replace(/^(the|a|an)\s+/iu, '')
    .replace(/\s+/gu, ' ')
    .trim();
}

function toPascal(value: string): string {
  return value
    .replace(/[^a-z0-9]+/giu, ' ')
    .trim()
    .split(/\s+/u)
    .filter((part) => part.length > 0)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join('');
}
