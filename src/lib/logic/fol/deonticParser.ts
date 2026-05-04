import {
  buildDeonticFormula,
  parseDeonticText,
  type DeonticParsedNorm,
  type DeonticParserOptions,
} from '../deontic/parser';
import { formatDeontic, type FormattedDeontic, type LogicOutputFormat } from './formatter';

type FolDeonticNormType = DeonticParsedNorm['norm_type'];
type FolDeonticOperator = DeonticParsedNorm['deontic_operator'];
type FolDeonticMetadata = {
  parser: 'browser-native-fol-deontic-parser';
  sourceModule: 'logic/fol/utils/deontic_parser.py';
  browserNative: true;
  pythonRuntime: false;
  serverCallsAllowed: false;
  outputFormat: LogicOutputFormat;
};
type FolDeonticSummary = {
  source_length: number;
  sentence_count: number;
  formula_count: number;
  norm_counts: Record<FolDeonticNormType, number>;
  conversion_rate: number;
};

export interface FolDeonticParserOptions extends DeonticParserOptions {
  outputFormat?: LogicOutputFormat;
  includeMetadata?: boolean;
}

export interface FolDeonticFormulaRecord {
  original_text: string;
  fol_formula: string;
  deontic_formula: string;
  norm_type: FolDeonticNormType;
  deontic_operator: FolDeonticOperator;
  subjects: string[];
  actions: string[];
  conditions: string[];
  exceptions: string[];
  temporal_constraints: DeonticParsedNorm['temporal_constraints'];
  confidence: number;
  sentence_index: number;
  start_offset: number;
  end_offset: number;
  formatted: FormattedDeontic;
}

export interface FolDeonticParseResult {
  success: boolean;
  formulas: FolDeonticFormulaRecord[];
  obligations: FolDeonticFormulaRecord[];
  permissions: FolDeonticFormulaRecord[];
  prohibitions: FolDeonticFormulaRecord[];
  summary: FolDeonticSummary;
  metadata: FolDeonticMetadata;
}

export function parseFolDeonticText(
  text: string,
  options: FolDeonticParserOptions = {},
): FolDeonticParseResult {
  const parsed = parseDeonticText(text, options);
  const outputFormat = options.outputFormat ?? 'json';
  const formulas = parsed.norms.map((norm) =>
    toFolDeonticFormulaRecord(norm, outputFormat, options.includeMetadata ?? true),
  );
  const sentenceCount = parsed.metadata.sentenceCount;
  const metadata: FolDeonticMetadata = {
    parser: 'browser-native-fol-deontic-parser',
    sourceModule: 'logic/fol/utils/deontic_parser.py',
    browserNative: true,
    pythonRuntime: false,
    serverCallsAllowed: false,
    outputFormat,
  };

  return {
    success: formulas.length > 0,
    formulas,
    obligations: formulas.filter((formula) => formula.norm_type === 'obligation'),
    permissions: formulas.filter((formula) => formula.norm_type === 'permission'),
    prohibitions: formulas.filter((formula) => formula.norm_type === 'prohibition'),
    summary: {
      source_length: text.length,
      sentence_count: sentenceCount,
      formula_count: formulas.length,
      norm_counts: parsed.metadata.normCounts,
      conversion_rate: sentenceCount > 0 ? formulas.length / sentenceCount : 0,
    },
    metadata,
  };
}

export function deonticTextToFolRecords(
  text: string,
  options: FolDeonticParserOptions = {},
): FolDeonticFormulaRecord[] {
  return parseFolDeonticText(text, options).formulas;
}

export const parse_fol_deontic_text = parseFolDeonticText;
export const parse_deontic_text_to_fol = parseFolDeonticText;
export const deontic_text_to_fol_records = deonticTextToFolRecords;
export const parseDeonticTextToFol = parseFolDeonticText;

function toFolDeonticFormulaRecord(
  norm: DeonticParsedNorm,
  outputFormat: LogicOutputFormat,
  includeMetadata: boolean,
): FolDeonticFormulaRecord {
  const element = {
    text: norm.text,
    sentenceIndex: norm.sentence_index,
    startOffset: norm.start_offset,
    endOffset: norm.end_offset,
    normType: norm.norm_type,
    deonticOperator: norm.deontic_operator,
    matchedIndicator: norm.indicator,
    subjects: norm.subjects,
    actions: norm.actions,
    conditions: norm.conditions,
    exceptions: norm.exceptions,
    temporalConstraints: norm.temporal_constraints,
    confidence: norm.confidence,
  };
  const deonticFormula = buildDeonticFormula(element);

  return {
    original_text: norm.text,
    fol_formula: stripOuterDeonticOperator(deonticFormula),
    deontic_formula: deonticFormula,
    norm_type: norm.norm_type,
    deontic_operator: norm.deontic_operator,
    subjects: norm.subjects,
    actions: norm.actions,
    conditions: norm.conditions,
    exceptions: norm.exceptions,
    temporal_constraints: norm.temporal_constraints,
    confidence: norm.confidence,
    sentence_index: norm.sentence_index,
    start_offset: norm.start_offset,
    end_offset: norm.end_offset,
    formatted: formatDeontic(deonticFormula, norm.norm_type, outputFormat, includeMetadata),
  };
}

function stripOuterDeonticOperator(formula: string): string {
  const operatorMatch = formula.match(/^[OPF]\((.*)\)$/);
  return operatorMatch ? operatorMatch[1] : formula;
}
