import { parseFolUtilityText, validateFolSyntax } from '../../fol/parser';
import { analyzeInteractiveFolInput } from './interactiveFolUtils';

export interface FolConstructorIoMetadata {
  sourcePythonModule: 'logic/integration/interactive/_fol_constructor_io.py';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
  runtimeDependencies: Array<string>;
}

export interface FolConstructorPrompt {
  id: string;
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface FolConstructorTurn {
  prompt: FolConstructorPrompt;
  formula: string;
  valid: boolean;
  warnings: Array<string>;
}

export interface FolConstructorSession {
  id: string;
  prompts: Array<FolConstructorPrompt>;
  turns: Array<FolConstructorTurn>;
  metadata: FolConstructorIoMetadata;
}

export interface FolConstructorIoResult {
  ok: boolean;
  session: FolConstructorSession;
  formula: string;
  errors: Array<string>;
  metadata: FolConstructorIoMetadata;
}

export interface InteractiveFolConstructorMetadata {
  sourcePythonModule: 'logic/integration/interactive/interactive_fol_constructor.py';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
  runtimeDependencies: Array<string>;
}

export type InteractiveFolQuestionReason =
  | 'empty_input'
  | 'invalid_formula'
  | 'missing_quantifier'
  | 'missing_relation';

export interface InteractiveFolQuestion {
  id: string;
  reason: InteractiveFolQuestionReason;
}
export interface InteractiveFolSymbol {
  name: string;
  kind: 'predicate' | 'variable';
}
export interface InteractiveFolConstructionOptions {
  sessionId?: string;
  role?: FolConstructorPrompt['role'];
}

export interface InteractiveFolConstructionResult {
  ok: boolean;
  session: FolConstructorSession;
  formula: string;
  questions: Array<InteractiveFolQuestion>;
  symbols: Array<InteractiveFolSymbol>;
  errors: Array<string>;
  metadata: InteractiveFolConstructorMetadata;
}

export const FOL_CONSTRUCTOR_IO_METADATA: FolConstructorIoMetadata = {
  sourcePythonModule: 'logic/integration/interactive/_fol_constructor_io.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntime: false,
  runtimeDependencies: [],
};

export const INTERACTIVE_FOL_CONSTRUCTOR_METADATA: InteractiveFolConstructorMetadata = {
  sourcePythonModule: 'logic/integration/interactive/interactive_fol_constructor.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntime: false,
  runtimeDependencies: [],
};

export class BrowserNativeFolConstructorIo {
  readonly metadata = FOL_CONSTRUCTOR_IO_METADATA;

  createSession(id = 'browser-native-fol-constructor'): FolConstructorSession {
    return { id, prompts: [], turns: [], metadata: this.metadata };
  }

  normalizePrompt(
    input: string | FolConstructorPrompt,
    role: FolConstructorPrompt['role'] = 'user',
  ): FolConstructorPrompt {
    if (typeof input !== 'string') {
      return {
        id: input.id.trim() || promptId(input.content),
        role: input.role,
        content: input.content.trim(),
      };
    }
    const content = input.trim();
    return { id: promptId(content), role, content };
  }

  appendPrompt(
    session: FolConstructorSession,
    input: string | FolConstructorPrompt,
    role: FolConstructorPrompt['role'] = 'user',
  ): FolConstructorIoResult {
    const prompt = this.normalizePrompt(input, role);
    if (!prompt.content) return this.result(session, '', ['empty_prompt']);
    const parsed = parseFolUtilityText(prompt.content, { failOnInvalid: true });
    const formula = parsed.formula || prompt.content;
    const validation = validateFolSyntax(formula);
    const turn = { prompt, formula, valid: validation.valid, warnings: parsed.warnings };
    const nextSession = {
      ...session,
      prompts: [...session.prompts, prompt],
      turns: [...session.turns, turn],
      metadata: this.metadata,
    };
    const errors = validation.valid ? [] : validation.issues.map((issue) => issue.message);
    return this.result(nextSession, formula, errors);
  }

  serializeSession(session: FolConstructorSession): string {
    return JSON.stringify({ ...session, metadata: this.metadata });
  }

  parseSession(json: string): FolConstructorIoResult {
    try {
      const value = JSON.parse(json) as Partial<FolConstructorSession>;
      if (
        typeof value.id !== 'string' ||
        !Array.isArray(value.prompts) ||
        !Array.isArray(value.turns)
      ) {
        return this.result(this.createSession('invalid-session'), '', ['invalid_session_shape']);
      }
      const prompts = value.prompts.map((prompt) => this.normalizePrompt(prompt));
      const turns = value.turns.filter(isTurn);
      return this.result(
        { id: value.id, prompts, turns, metadata: this.metadata },
        turns[turns.length - 1]?.formula ?? '',
        [],
      );
    } catch {
      return this.result(this.createSession('invalid-json'), '', ['invalid_json']);
    }
  }

  private result(
    session: FolConstructorSession,
    formula: string,
    errors: Array<string>,
  ): FolConstructorIoResult {
    return { ok: errors.length === 0, session, formula, errors, metadata: this.metadata };
  }
}

export function createBrowserNativeFolConstructorIo(): BrowserNativeFolConstructorIo {
  return new BrowserNativeFolConstructorIo();
}

export class BrowserNativeInteractiveFolConstructor {
  readonly metadata = INTERACTIVE_FOL_CONSTRUCTOR_METADATA;
  private readonly io: BrowserNativeFolConstructorIo;

  constructor(io = createBrowserNativeFolConstructorIo()) {
    this.io = io;
  }

  construct(
    text: string,
    options: InteractiveFolConstructionOptions = {},
  ): InteractiveFolConstructionResult {
    const session = this.io.createSession(options.sessionId ?? 'browser-native-interactive-fol');
    return this.continueSession(session, text, options);
  }

  continueSession(
    session: FolConstructorSession,
    text: string,
    options: InteractiveFolConstructionOptions = {},
  ): InteractiveFolConstructionResult {
    const ioResult = this.io.appendPrompt(session, text, options.role ?? 'user');
    return this.fromIoResult(text, ioResult);
  }

  private fromIoResult(
    sourceText: string,
    ioResult: FolConstructorIoResult,
  ): InteractiveFolConstructionResult {
    const analysis = analyzeInteractiveFolInput(sourceText, ioResult.formula, ioResult.errors);
    const errors = [...ioResult.errors];
    return {
      ok:
        errors.length === 0 &&
        analysis.questions.every((question) => question.reason !== 'empty_input'),
      session: ioResult.session,
      formula: ioResult.formula,
      questions: analysis.questions,
      symbols: analysis.symbols,
      errors,
      metadata: this.metadata,
    };
  }
}

export function createBrowserNativeInteractiveFolConstructor(): BrowserNativeInteractiveFolConstructor {
  return new BrowserNativeInteractiveFolConstructor();
}

export const create_browser_native_fol_constructor_io = createBrowserNativeFolConstructorIo;
export const fol_constructor_io_metadata = FOL_CONSTRUCTOR_IO_METADATA;
export const create_browser_native_interactive_fol_constructor =
  createBrowserNativeInteractiveFolConstructor;
export const interactive_fol_constructor_metadata = INTERACTIVE_FOL_CONSTRUCTOR_METADATA;

function promptId(content: string): string {
  const normalized = content
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
  return normalized ? `prompt-${normalized.slice(0, 48)}` : 'prompt-empty';
}

function isTurn(value: unknown): value is FolConstructorTurn {
  if (!value || typeof value !== 'object') return false;
  const turn = value as Partial<FolConstructorTurn>;
  return (
    typeof turn.formula === 'string' &&
    typeof turn.valid === 'boolean' &&
    Array.isArray(turn.warnings)
  );
}

function buildInteractiveQuestions(
  text: string,
  parsed: ReturnType<typeof parseFolUtilityText>,
  formula: string,
  errors: Array<string>,
): Array<InteractiveFolQuestion> {
  if (!text.trim()) {
    return [
      {
        id: 'question-empty-input',
        reason: 'empty_input',
      },
    ];
  }
  if (errors.length > 0 || !parsed.validation.valid) {
    return [
      {
        id: 'question-invalid-formula',
        reason: 'invalid_formula',
      },
    ];
  }
  const questions: Array<InteractiveFolQuestion> = [];
  if (parsed.quantifiers.length === 0 && !/[∀∃]/.test(formula)) {
    questions.push({
      id: 'question-missing-quantifier',
      reason: 'missing_quantifier',
    });
  }
  if (parsed.operators.length === 0 && parsed.clauses.length <= 1) {
    questions.push({
      id: 'question-missing-relation',
      reason: 'missing_relation',
    });
  }
  return questions;
}

function extractFormulaSymbols(formula: string): Array<InteractiveFolSymbol> {
  const symbols = new Map<string, InteractiveFolSymbol>();
  for (const match of formula.matchAll(/\b([A-Z][A-Za-z0-9_]*)\s*\(/g)) {
    symbols.set(`predicate:${match[1]}`, { name: match[1], kind: 'predicate' });
  }
  for (const match of formula.matchAll(/[∀∃]([a-z][A-Za-z0-9_]*)/g)) {
    symbols.set(`variable:${match[1]}`, { name: match[1], kind: 'variable' });
  }
  return [...symbols.values()];
}
