import { parseFolUtilityText, validateFolSyntax } from '../../fol/parser';

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

export const FOL_CONSTRUCTOR_IO_METADATA: FolConstructorIoMetadata = {
  sourcePythonModule: 'logic/integration/interactive/_fol_constructor_io.py',
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

export const create_browser_native_fol_constructor_io = createBrowserNativeFolConstructorIo;
export const fol_constructor_io_metadata = FOL_CONSTRUCTOR_IO_METADATA;

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
