import type { TdfolLlmOperatorHint } from './browserNativeLlm';
import { getTdfolOperatorHintsForText } from './browserNativeLlm';

export type TdfolNlContextEntity = {
  id: string;
  label: string;
  kind: 'subject' | 'object';
  mentions: number;
  lastMentionIndex: number;
};
export type TdfolNlContextAction = {
  id: string;
  label: string;
  operatorHints: TdfolLlmOperatorHint[];
  mentions: number;
  lastMentionIndex: number;
};
export type TdfolNlContextTurn = {
  index: number;
  input: string;
  normalized: string;
  resolvedText: string;
  entityIds: string[];
  actionIds: string[];
};
export type TdfolNlContextSnapshot = {
  turns: TdfolNlContextTurn[];
  entities: TdfolNlContextEntity[];
  actions: TdfolNlContextAction[];
  focusEntity: TdfolNlContextEntity | null;
  focusAction: TdfolNlContextAction | null;
  metadata: { browserNative: true; serverCallsAllowed: false; pythonRuntime: false };
};

const METADATA = { browserNative: true, serverCallsAllowed: false, pythonRuntime: false } as const;

export class BrowserNativeTdfolNlContext {
  private readonly turns: TdfolNlContextTurn[] = [];
  private readonly entities = new Map<string, TdfolNlContextEntity>();
  private readonly actions = new Map<string, TdfolNlContextAction>();
  private focusEntityId: string | null = null;
  private focusActionId: string | null = null;

  constructor(private readonly maxTurns = 24) {}

  addTurn(text: string): TdfolNlContextTurn {
    const normalized = normalizeSentence(text);
    const resolvedText = this.resolveText(normalized);
    const parsed = parseUniversalPolicy(resolvedText);
    const entityIds = parsed ? [this.recordEntity(parsed.subject).id] : [];
    const actionIds = parsed ? [this.recordAction(parsed.action, resolvedText).id] : [];
    const turn = {
      index: this.turns.length,
      input: text,
      normalized,
      resolvedText,
      entityIds,
      actionIds,
    };
    this.turns.push(turn);
    if (this.turns.length > this.maxTurns) this.turns.shift();
    return turn;
  }

  resolveText(text: string): string {
    const normalized = normalizeSentence(text);
    const focused = this.focusEntity();
    if (!focused) return normalized;
    const subject = pluralize(focused.label.toLowerCase());
    const replaced = normalized.replace(/^(they|them|it|he|she)\b/i, `All ${subject}`);
    if (replaced !== normalized) return ensureSentencePeriod(replaced);
    return /^(must|shall|may|can|are required to|are allowed to|must not|shall not)\b/i.test(
      normalized,
    )
      ? ensureSentencePeriod(`All ${subject} ${normalized}`)
      : normalized;
  }

  snapshot(): TdfolNlContextSnapshot {
    return {
      turns: this.turns.map((turn) => ({ ...turn })),
      entities: Array.from(this.entities.values()).map((entity) => ({ ...entity })),
      actions: Array.from(this.actions.values()).map((action) => ({ ...action })),
      focusEntity: this.focusEntity(),
      focusAction: this.focusAction(),
      metadata: METADATA,
    };
  }

  clear(): void {
    this.turns.length = 0;
    this.entities.clear();
    this.actions.clear();
    this.focusEntityId = null;
    this.focusActionId = null;
  }

  private focusEntity(): TdfolNlContextEntity | null {
    return this.focusEntityId ? (this.entities.get(this.focusEntityId) ?? null) : null;
  }

  private focusAction(): TdfolNlContextAction | null {
    return this.focusActionId ? (this.actions.get(this.focusActionId) ?? null) : null;
  }

  private recordEntity(label: string): TdfolNlContextEntity {
    const id = stableId(singularize(label));
    const entity = this.entities.get(id) ?? {
      id,
      label: titleWords(singularize(label)),
      kind: 'subject' as const,
      mentions: 0,
      lastMentionIndex: 0,
    };
    entity.mentions += 1;
    entity.lastMentionIndex = this.turns.length;
    this.entities.set(id, entity);
    this.focusEntityId = id;
    return entity;
  }

  private recordAction(label: string, text: string): TdfolNlContextAction {
    const id = stableId(label);
    const action = this.actions.get(id) ?? {
      id,
      label: titleWords(label),
      operatorHints: getTdfolOperatorHintsForText(text),
      mentions: 0,
      lastMentionIndex: 0,
    };
    action.mentions += 1;
    action.lastMentionIndex = this.turns.length;
    this.actions.set(id, action);
    this.focusActionId = id;
    return action;
  }
}

export function createBrowserNativeTdfolNlContext(maxTurns?: number): BrowserNativeTdfolNlContext {
  return new BrowserNativeTdfolNlContext(maxTurns);
}

export function resolveTdfolNlContextText(
  text: string,
  context: BrowserNativeTdfolNlContext,
): string {
  return context.resolveText(text);
}

function parseUniversalPolicy(text: string): { subject: string; action: string } | null {
  const match = text
    .toLowerCase()
    .replace(/[.]/g, '')
    .trim()
    .match(
      /^(?:all|every|each)\s+([a-z ]+?)\s+(?:must not|shall not|must|shall|may|can|is required to|is allowed to|are required to|are allowed to)\s+(.+)$/,
    );
  return match ? { subject: match[1], action: match[2].replace(/^not\s+/, '') } : null;
}

function normalizeSentence(text: string): string {
  return ensureSentencePeriod(text.trim().replace(/\s+/g, ' '));
}
function ensureSentencePeriod(text: string): string {
  return /[.!?]$/.test(text) ? text : `${text}.`;
}
function stableId(label: string): string {
  return label
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}
function singularize(label: string): string {
  return label.trim().replace(/\s+/g, ' ').replace(/ies$/i, 'y').replace(/s$/i, '');
}
function pluralize(label: string): string {
  return label.endsWith('y')
    ? `${label.slice(0, -1)}ies`
    : label.endsWith('s')
      ? label
      : `${label}s`;
}
function titleWords(label: string): string {
  return label
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(' ');
}
