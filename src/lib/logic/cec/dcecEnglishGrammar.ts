import {
  DcecAtomicFormula,
  DcecCognitiveFormula,
  DcecConnectiveFormula,
  DcecDeonticFormula,
  DcecFormula,
  DcecTemporalFormula,
  DcecTerm,
  DcecVariableTerm,
} from './dcecCore';
import { DcecNamespace } from './dcecNamespace';
import {
  DcecCognitiveOperator,
  DcecCognitiveOperatorValue,
  DcecDeonticOperator,
  DcecDeonticOperatorValue,
  DcecLogicalConnective,
  DcecLogicalConnectiveValue,
  DcecPredicateSymbol,
  DcecTemporalOperator,
  DcecTemporalOperatorValue,
} from './dcecTypes';
import {
  CecGrammarCategory,
  CecGrammarEngine,
  CecGrammarRule,
  CecLexicalEntry,
} from './grammarEngine';
import { createDomainVocabulary, normalizeDomainPredicate } from './domainVocabulary';

export interface DcecEnglishSemanticRecord {
  type: string;
  [key: string]: unknown;
}

export interface DcecNativeEnglishGrammarCapabilities {
  readonly browserNative: true;
  readonly pythonRuntime: false;
  readonly serverRuntime: false;
  readonly filesystem: false;
  readonly subprocess: false;
  readonly rpc: false;
  readonly wasmCompatible: true;
  readonly wasmRequired: false;
  readonly implementation: 'deterministic-typescript';
  readonly pythonModule: 'logic/CEC/native/dcec_english_grammar.py';
}

export interface DcecNativeEnglishGrammarOptions {
  readonly maxInputLength?: number;
}

export interface DcecNativeEnglishGrammarParseResult {
  readonly ok: boolean;
  readonly input: string;
  readonly normalizedInput: string;
  readonly formula?: DcecFormula;
  readonly dcec?: string;
  readonly semantic?: DcecEnglishSemanticRecord;
  readonly ruleNames: readonly string[];
  readonly lexicalWords: readonly string[];
  readonly errors: readonly string[];
  readonly metadata: {
    readonly sourcePythonModule: 'logic/CEC/native/dcec_english_grammar.py';
    readonly runtime: 'browser-native-typescript';
    readonly implementation: 'deterministic-dcec-english-grammar';
  };
}

type DcecEnglishSemanticValue = DcecEnglishSemanticRecord | string | number | boolean | undefined;

const COMMON_AGENTS = ['jack', 'robot', 'alice', 'bob', 'system'];
const COMMON_ACTIONS = ['laugh', 'sleep', 'run', 'eat', 'walk', 'talk', 'work'];
const COMMON_FLUENTS = ['happy', 'sad', 'hungry', 'tired', 'sick', 'angry'];
const DOMAIN_VOCABULARY = createDomainVocabulary();
const DEFAULT_NATIVE_MAX_INPUT_LENGTH = 4096;
const NATIVE_GRAMMAR_METADATA = {
  sourcePythonModule: 'logic/CEC/native/dcec_english_grammar.py',
  runtime: 'browser-native-typescript',
  implementation: 'deterministic-dcec-english-grammar',
} as const;
const NATIVE_GRAMMAR_CAPABILITIES: DcecNativeEnglishGrammarCapabilities = {
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
  filesystem: false,
  subprocess: false,
  rpc: false,
  wasmCompatible: true,
  wasmRequired: false,
  implementation: 'deterministic-typescript',
  pythonModule: 'logic/CEC/native/dcec_english_grammar.py',
};

export class DcecEnglishGrammar {
  readonly engine = new CecGrammarEngine();
  readonly namespace: DcecNamespace;

  constructor(namespace = new DcecNamespace()) {
    this.namespace = namespace;
    this.engine.startCategory = 'Boolean';
    this.setupLexicon();
    this.setupRules();
  }

  parseToDcec(text: string): DcecFormula | undefined {
    const parse = this.engine.resolveAmbiguity(this.engine.parse(text), 'first');
    const formula = parse ? this.semanticToFormula(parse.semantics) : undefined;
    return formula ?? this.patternParseToDcec(text);
  }

  formulaToEnglish(formula: DcecFormula): string {
    return this.linearizeBoolean(this.formulaToSemantic(formula));
  }

  semanticToFormula(semanticValue: unknown): DcecFormula | undefined {
    if (!isSemanticRecord(semanticValue)) return undefined;

    if (semanticValue.type === 'connective') {
      const operator = normalizeConnective(semanticValue.operator);
      if (!operator) return undefined;
      if (operator === DcecLogicalConnective.NOT) {
        const inner = this.semanticToFormula(semanticValue.formula);
        return inner ? new DcecConnectiveFormula(operator, [inner]) : undefined;
      }
      const left = this.semanticToFormula(semanticValue.left);
      const right = this.semanticToFormula(semanticValue.right);
      return left && right ? new DcecConnectiveFormula(operator, [left, right]) : undefined;
    }

    if (semanticValue.type === 'atomic') {
      const predicateName = stringName(semanticValue.predicate);
      if (!predicateName) return undefined;
      const args = toSemanticArray(semanticValue.arguments).map((arg, index) =>
        this.agentTerm(nameFromSemantic(arg) ?? `arg${index + 1}`),
      );
      return new DcecAtomicFormula(this.predicate(predicateName, args.length), args);
    }

    if (semanticValue.type === 'deontic') {
      const operator = normalizeDeontic(semanticValue.operator);
      if (!operator) return undefined;
      const formula = isSemanticRecord(semanticValue.formula)
        ? this.semanticToFormula(semanticValue.formula)
        : this.actionSemanticToFormula(semanticValue);
      if (!formula) return undefined;
      const agentName = nameFromSemantic(semanticValue.agent);
      return new DcecDeonticFormula(
        operator,
        formula,
        agentName ? this.agentTerm(agentName) : undefined,
      );
    }

    if (semanticValue.type === 'cognitive') {
      const operator = normalizeCognitive(semanticValue.operator);
      const proposition = this.semanticToFormula(semanticValue.proposition);
      const agentName = nameFromSemantic(semanticValue.agent);
      return operator && proposition && agentName
        ? new DcecCognitiveFormula(operator, this.agentTerm(agentName), proposition)
        : undefined;
    }

    if (semanticValue.type === 'temporal') {
      const operator = normalizeTemporal(semanticValue.operator);
      const proposition = this.semanticToFormula(semanticValue.proposition);
      return operator && proposition ? new DcecTemporalFormula(operator, proposition) : undefined;
    }

    return undefined;
  }

  formulaToSemantic(formula: DcecFormula): DcecEnglishSemanticRecord {
    if (formula instanceof DcecAtomicFormula) {
      return {
        type: 'atomic',
        predicate: formula.predicate.name,
        arguments: formula.arguments.map((arg) => ({ type: 'agent', name: termName(arg) })),
      };
    }
    if (formula instanceof DcecConnectiveFormula) {
      if (formula.connective === DcecLogicalConnective.NOT) {
        return {
          type: 'connective',
          operator: formula.connective,
          formula: this.formulaToSemantic(formula.formulas[0]),
        };
      }
      return {
        type: 'connective',
        operator: formula.connective,
        left: this.formulaToSemantic(formula.formulas[0]),
        right: this.formulaToSemantic(formula.formulas[1]),
      };
    }
    if (formula instanceof DcecDeonticFormula) {
      return {
        type: 'deontic',
        operator: formula.operator,
        formula: this.formulaToSemantic(formula.formula),
        ...(formula.agent ? { agent: { type: 'agent', name: termName(formula.agent) } } : {}),
      };
    }
    if (formula instanceof DcecCognitiveFormula) {
      return {
        type: 'cognitive',
        operator: formula.operator,
        agent: { type: 'agent', name: termName(formula.agent) },
        proposition: this.formulaToSemantic(formula.formula),
      };
    }
    if (formula instanceof DcecTemporalFormula) {
      return {
        type: 'temporal',
        operator: formula.operator,
        proposition: this.formulaToSemantic(formula.formula),
      };
    }
    return { type: 'unknown', formula: formula.toString() };
  }

  linearizeBoolean(semanticValue: DcecEnglishSemanticValue): string {
    if (!isSemanticRecord(semanticValue)) return String(semanticValue);
    if (semanticValue.type === 'connective') return this.linearizeConnective(semanticValue);
    if (semanticValue.type === 'deontic') return this.linearizeDeontic(semanticValue);
    if (semanticValue.type === 'cognitive') {
      const agent = nameFromSemantic(semanticValue.agent) ?? '?';
      return `${agent} ${String(semanticValue.operator)} ${this.linearizeBoolean(semanticValue.proposition as DcecEnglishSemanticValue)}`;
    }
    if (semanticValue.type === 'temporal') {
      return `${String(semanticValue.operator)} ${this.linearizeBoolean(semanticValue.proposition as DcecEnglishSemanticValue)}`;
    }
    if (semanticValue.type === 'atomic') {
      const predicate = stringName(semanticValue.predicate) ?? '?';
      const firstArg = nameFromSemantic(toSemanticArray(semanticValue.arguments)[0]);
      return firstArg ? `${firstArg} ${predicate}` : predicate;
    }
    return JSON.stringify(semanticValue);
  }

  getLexicalWords(): string[] {
    return [...this.engine.lexicon.keys()];
  }

  getRuleNames(): string[] {
    return this.engine.rules.map((rule) => rule.name);
  }

  getNativeParityCapabilities(): DcecNativeEnglishGrammarCapabilities {
    return NATIVE_GRAMMAR_CAPABILITIES;
  }

  parseNativeEnglishGrammar(
    text: string,
    options: DcecNativeEnglishGrammarOptions = {},
  ): DcecNativeEnglishGrammarParseResult {
    const normalizedInput =
      typeof text === 'string' ? text.trim().toLowerCase().replace(/\s+/g, ' ') : '';
    const maxInputLength = options.maxInputLength ?? DEFAULT_NATIVE_MAX_INPUT_LENGTH;
    const baseResult = {
      input: text,
      normalizedInput,
      ruleNames: this.getRuleNames(),
      lexicalWords: this.getLexicalWords(),
      metadata: NATIVE_GRAMMAR_METADATA,
    };

    if (typeof text !== 'string') {
      return { ...baseResult, ok: false, errors: ['Input must be a string'] };
    }
    if (normalizedInput.length === 0) {
      return { ...baseResult, ok: false, errors: ['Input must not be empty'] };
    }
    if (normalizedInput.length > maxInputLength) {
      return {
        ...baseResult,
        ok: false,
        errors: [`Input exceeds maximum length of ${maxInputLength} characters`],
      };
    }

    const formula = this.parseToDcec(normalizedInput);
    if (!formula) {
      return {
        ...baseResult,
        ok: false,
        errors: ['Unable to parse English input with native DCEC grammar'],
      };
    }

    return {
      ...baseResult,
      ok: true,
      formula,
      dcec: formula.toString(),
      semantic: this.formulaToSemantic(formula),
      errors: [],
    };
  }

  private setupLexicon(): void {
    this.addWords(['and'], 'Conj', { type: 'and', connective: DcecLogicalConnective.AND });
    this.addWords(['or'], 'Conj', { type: 'or', connective: DcecLogicalConnective.OR });
    this.addWords(['if'], 'Conj', { type: 'if', connective: DcecLogicalConnective.IMPLIES });
    this.addWords(['then'], 'Conj', { type: 'then' });
    this.addWords(['not'], 'Adv', { type: 'not', connective: DcecLogicalConnective.NOT });

    this.addWords(['must', 'shall', 'obligated', 'should', 'required'], 'V', {
      type: 'deontic',
      operator: 'obligated',
    });
    this.addWords(['forbidden', 'prohibited'], 'V', { type: 'deontic', operator: 'forbidden' });
    this.addWords(['may', 'permitted', 'allowed'], 'V', { type: 'deontic', operator: 'permitted' });

    this.addWords(['believes', 'belief'], 'V', { type: 'cognitive', operator: 'believes' });
    this.addWords(['knows', 'knowledge'], 'V', { type: 'cognitive', operator: 'knows' });
    this.addWords(['intends', 'intention'], 'V', { type: 'cognitive', operator: 'intends' });
    this.addWords(['desires', 'desire'], 'V', { type: 'cognitive', operator: 'desires' });

    this.addWords(['always', 'necessarily'], 'Adv', { type: 'temporal', operator: 'always' });
    this.addWords(['eventually', 'finally', 'someday'], 'Adv', {
      type: 'temporal',
      operator: 'eventually',
    });
    this.addWords(['next'], 'Adv', { type: 'temporal', operator: 'next' });
    this.addWords(['until'], 'Prep', { type: 'temporal', operator: 'until' });

    this.addWords(['all', 'every'], 'Det', { type: 'quantifier', operator: 'forall' });
    this.addWords(['some', 'any'], 'Det', { type: 'quantifier', operator: 'exists' });
    this.addWords(['is', 'are', 'was', 'were', 'be', 'been', 'being'], 'V', { type: 'auxiliary' });
    this.addWords(['to', 'the', 'a', 'an'], 'Det', { type: 'determiner' });

    for (const agent of [...COMMON_AGENTS, ...DOMAIN_VOCABULARY.agents])
      this.addWords([agent], 'Agent', { type: 'agent', name: agent });
    for (const action of [...COMMON_ACTIONS, ...DOMAIN_VOCABULARY.actions])
      this.addWords([action], 'ActionType', { type: 'action', name: action });
    for (const fluent of [...COMMON_FLUENTS, ...DOMAIN_VOCABULARY.fluents])
      this.addWords([fluent], 'Fluent', { type: 'fluent', name: fluent });
  }

  private setupRules(): void {
    this.engine.addRule(
      this.binaryRule('agent_action_rule', 'Boolean', 'Agent', 'ActionType', ([agent, action]) => ({
        type: 'atomic',
        predicate: nameFromSemantic(action),
        arguments: [agent],
      })),
    );
    this.engine.addRule(
      this.binaryRule('agent_fluent_rule', 'Boolean', 'Agent', 'Fluent', ([agent, fluent]) => ({
        type: 'atomic',
        predicate: nameFromSemantic(fluent),
        arguments: [agent],
      })),
    );
    this.engine.addRule(
      this.binaryRule('modal_agent_rule', 'VP', 'Agent', 'V', ([agent, modal]) => ({
        type: 'modal_agent',
        agent,
        modal,
      })),
    );
    this.engine.addRule(
      this.binaryRule('obligated_rule', 'Boolean', 'VP', 'ActionType', ([head, action]) =>
        modalActionSemantics(head, action),
      ),
    );
    this.engine.addRule(
      this.binaryRule('believes_rule', 'Boolean', 'VP', 'Boolean', ([head, proposition]) =>
        modalPropositionSemantics(head, proposition),
      ),
    );
    this.engine.addRule(
      this.binaryRule('always_rule', 'Boolean', 'Adv', 'Boolean', ([operator, proposition]) =>
        adverbSemantics(operator, proposition),
      ),
    );
    this.engine.addRule(
      this.binaryRule('not_rule', 'Boolean', 'Adv', 'Boolean', ([operator, proposition]) => {
        if (isSemanticRecord(operator) && operator.type === 'not') {
          return { type: 'connective', operator: DcecLogicalConnective.NOT, formula: proposition };
        }
        return adverbSemantics(operator, proposition);
      }),
    );
    this.engine.addRule(
      this.binaryRule('connective_left_rule', 'Cl', 'Boolean', 'Conj', ([left, connective]) => ({
        type: 'connective_head',
        left,
        connective,
      })),
    );
    this.engine.addRule(
      this.binaryRule('and_rule', 'Boolean', 'Cl', 'Boolean', ([head, right]) =>
        connectiveSemantics(head, right),
      ),
    );
    this.engine.addRule(
      this.binaryRule('or_rule', 'Boolean', 'Cl', 'Boolean', ([head, right]) =>
        connectiveSemantics(head, right),
      ),
    );
    this.engine.addRule(
      this.binaryRule('implies_rule', 'Boolean', 'Cl', 'Boolean', ([head, right]) =>
        connectiveSemantics(head, right),
      ),
    );
  }

  private patternParseToDcec(text: string): DcecFormula | undefined {
    const normalized = text.trim().toLowerCase().replace(/\s+/g, ' ');
    const connective =
      normalized.match(/^if (.+) then (.+)$/) ?? normalized.match(/^(.+) (and|or) (.+)$/);
    if (connective) {
      const op =
        connective[2] === 'and'
          ? DcecLogicalConnective.AND
          : connective[2] === 'or'
            ? DcecLogicalConnective.OR
            : DcecLogicalConnective.IMPLIES;
      const left = this.parseToDcec(connective[1]);
      const right = this.parseToDcec(connective[3] ?? connective[2]);
      return left && right ? new DcecConnectiveFormula(op, [left, right]) : undefined;
    }

    const temporal = normalized.match(/^(always|eventually|next) (.+)$/);
    if (temporal) {
      const inner = this.parseToDcec(temporal[2]);
      const op = normalizeTemporal(temporal[1]);
      return inner && op ? new DcecTemporalFormula(op, inner) : undefined;
    }

    const cognitive = normalized.match(
      /^(\w+) (believes|knows|intends|desires)(?: that| to)? (.+)$/,
    );
    if (cognitive) {
      const inner = this.parseToDcec(cognitive[3]) ?? this.atomic(cognitive[3], cognitive[1]);
      const op = normalizeCognitive(cognitive[2]);
      return op ? new DcecCognitiveFormula(op, this.agentTerm(cognitive[1]), inner) : undefined;
    }

    const deontic = normalized.match(
      /^(\w+) (must|shall|should|may|forbidden|prohibited|permitted|allowed)(?: to)? (.+)$/,
    );
    if (deontic) {
      const op = normalizeDeontic(deontic[2]);
      if (!op) return undefined;
      const actionText = deontic[3].trim();
      const effectiveOperator =
        op === DcecDeonticOperator.OBLIGATION && actionText.startsWith('not ')
          ? DcecDeonticOperator.PROHIBITION
          : op;
      const effectiveAction =
        effectiveOperator === DcecDeonticOperator.PROHIBITION && actionText.startsWith('not ')
          ? actionText.slice(4)
          : actionText;
      return new DcecDeonticFormula(
        effectiveOperator,
        this.atomic(effectiveAction, deontic[1]),
        this.agentTerm(deontic[1]),
      );
    }

    const action = normalized.match(/^(\w+) (.+)$/);
    return action ? this.atomic(action[2], action[1]) : undefined;
  }

  private actionSemanticToFormula(
    semanticValue: DcecEnglishSemanticRecord,
  ): DcecFormula | undefined {
    const actionName = nameFromSemantic(semanticValue.action);
    const agentName = nameFromSemantic(semanticValue.agent);
    if (!actionName || !agentName) return undefined;
    return this.atomic(actionName, agentName);
  }

  private atomic(predicateName: string, agentName: string): DcecAtomicFormula {
    const normalizedPredicate = normalizeDomainPredicate(predicateName, DOMAIN_VOCABULARY);
    return new DcecAtomicFormula(this.predicate(normalizedPredicate, 1), [
      this.agentTerm(agentName),
    ]);
  }

  private predicate(name: string, arity: number): DcecPredicateSymbol {
    const existing = this.namespace.getPredicate(name);
    if (existing && existing.arity() === arity) return existing;
    const sorts = Array.from({ length: arity }, () => this.namespace.getSort('Agent')!);
    return new DcecPredicateSymbol(name, sorts);
  }

  private agentTerm(name: string): DcecVariableTerm {
    const variable = this.namespace.getVariable(name) ?? this.namespace.addVariable(name, 'Agent');
    return new DcecVariableTerm(variable);
  }

  private addWords(
    words: string[],
    category: CecGrammarCategory,
    semantics: DcecEnglishSemanticRecord,
  ): void {
    for (const word of words) {
      this.engine.addLexicalEntry(
        new CecLexicalEntry({
          word,
          category,
          semantics: { ...semantics, word },
        }),
      );
    }
  }

  private binaryRule(
    name: string,
    category: CecGrammarCategory,
    left: CecGrammarCategory,
    right: CecGrammarCategory,
    semanticFn: (values: unknown[]) => unknown,
  ): CecGrammarRule {
    return new CecGrammarRule({
      name,
      category,
      constituents: [left, right],
      semanticFn,
      linearizeFn: (semanticValue) =>
        this.linearizeBoolean(semanticValue as DcecEnglishSemanticValue),
    });
  }

  private linearizeConnective(semanticValue: DcecEnglishSemanticRecord): string {
    const operator = normalizeConnective(semanticValue.operator);
    if (operator === DcecLogicalConnective.NOT) {
      return `not ${this.linearizeBoolean(semanticValue.formula as DcecEnglishSemanticValue)}`;
    }
    const left = this.linearizeBoolean(semanticValue.left as DcecEnglishSemanticValue);
    const right = this.linearizeBoolean(semanticValue.right as DcecEnglishSemanticValue);
    if (operator === DcecLogicalConnective.IMPLIES) return `if ${left} then ${right}`;
    return `(${left} ${operator ?? String(semanticValue.operator)} ${right})`;
  }

  private linearizeDeontic(semanticValue: DcecEnglishSemanticRecord): string {
    if (isSemanticRecord(semanticValue.formula)) {
      const prefix: Record<string, unknown> = {
        [DcecDeonticOperator.OBLIGATION]: 'It is obligatory that',
        [DcecDeonticOperator.PERMISSION]: 'It is permitted that',
        [DcecDeonticOperator.PROHIBITION]: 'It is forbidden that',
      };
      return `${prefix[String(semanticValue.operator)] ?? `[${String(semanticValue.operator)}]`} ${this.linearizeBoolean(semanticValue.formula as DcecEnglishSemanticValue)}`;
    }

    const agent = nameFromSemantic(semanticValue.agent) ?? '?';
    const action = nameFromSemantic(semanticValue.action) ?? '?';
    const op = normalizeDeontic(semanticValue.operator);
    if (op === DcecDeonticOperator.OBLIGATION) return `${agent} must ${action}`;
    if (op === DcecDeonticOperator.PROHIBITION) return `${agent} is forbidden to ${action}`;
    if (op === DcecDeonticOperator.PERMISSION) return `${agent} may ${action}`;
    return `[${String(semanticValue.operator)}] ${agent} ${action}`;
  }
}

export function createDcecEnglishGrammar(namespace?: DcecNamespace): DcecEnglishGrammar {
  return new DcecEnglishGrammar(namespace);
}

export function getDcecNativeEnglishGrammarCapabilities(): DcecNativeEnglishGrammarCapabilities {
  return NATIVE_GRAMMAR_CAPABILITIES;
}

export function parseDcecNativeEnglishGrammar(
  text: string,
  options?: DcecNativeEnglishGrammarOptions,
): DcecNativeEnglishGrammarParseResult {
  return createDcecEnglishGrammar().parseNativeEnglishGrammar(text, options);
}

function modalActionSemantics(head: unknown, action: unknown): DcecEnglishSemanticRecord {
  if (!isSemanticRecord(head) || !isSemanticRecord(head.modal)) return { type: 'unknown' };
  const modal = head.modal;
  if (modal.type !== 'deontic') return { type: 'unknown' };
  return {
    type: 'deontic',
    operator: modal.operator,
    agent: head.agent,
    action,
  };
}

function modalPropositionSemantics(head: unknown, proposition: unknown): DcecEnglishSemanticRecord {
  if (!isSemanticRecord(head) || !isSemanticRecord(head.modal)) return { type: 'unknown' };
  const modal = head.modal;
  if (modal.type !== 'cognitive') return { type: 'unknown' };
  return {
    type: 'cognitive',
    operator: modal.operator,
    agent: head.agent,
    proposition,
  };
}

function adverbSemantics(operator: unknown, proposition: unknown): DcecEnglishSemanticRecord {
  if (!isSemanticRecord(operator) || operator.type !== 'temporal') return { type: 'unknown' };
  return {
    type: 'temporal',
    operator: operator.operator,
    proposition,
  };
}

function connectiveSemantics(head: unknown, right: unknown): DcecEnglishSemanticRecord {
  if (!isSemanticRecord(head) || !isSemanticRecord(head.connective)) return { type: 'unknown' };
  const connective = head.connective;
  return {
    type: 'connective',
    operator: connective.connective,
    left: head.left,
    right,
  };
}

function normalizeConnective(value: unknown): DcecLogicalConnectiveValue | undefined {
  const raw = String(value);
  if (raw === DcecLogicalConnective.AND || raw.toLowerCase() === 'and')
    return DcecLogicalConnective.AND;
  if (raw === DcecLogicalConnective.OR || raw.toLowerCase() === 'or')
    return DcecLogicalConnective.OR;
  if (raw === DcecLogicalConnective.NOT || raw.toLowerCase() === 'not')
    return DcecLogicalConnective.NOT;
  if (raw === DcecLogicalConnective.IMPLIES || raw.toLowerCase() === 'implies')
    return DcecLogicalConnective.IMPLIES;
  return undefined;
}

function normalizeDeontic(value: unknown): DcecDeonticOperatorValue | undefined {
  const raw = String(value).toLowerCase();
  if (
    value === DcecDeonticOperator.OBLIGATION ||
    ['obligated', 'must', 'shall', 'should', 'required'].includes(raw)
  )
    return DcecDeonticOperator.OBLIGATION;
  if (value === DcecDeonticOperator.PERMISSION || ['permitted', 'may', 'allowed'].includes(raw))
    return DcecDeonticOperator.PERMISSION;
  if (value === DcecDeonticOperator.PROHIBITION || ['forbidden', 'prohibited'].includes(raw))
    return DcecDeonticOperator.PROHIBITION;
  return undefined;
}

function normalizeCognitive(value: unknown): DcecCognitiveOperatorValue | undefined {
  const raw = String(value).toLowerCase();
  if (value === DcecCognitiveOperator.BELIEF || ['believes', 'belief'].includes(raw))
    return DcecCognitiveOperator.BELIEF;
  if (value === DcecCognitiveOperator.KNOWLEDGE || ['knows', 'knowledge'].includes(raw))
    return DcecCognitiveOperator.KNOWLEDGE;
  if (value === DcecCognitiveOperator.INTENTION || ['intends', 'intention'].includes(raw))
    return DcecCognitiveOperator.INTENTION;
  if (value === DcecCognitiveOperator.DESIRE || ['desires', 'desire'].includes(raw))
    return DcecCognitiveOperator.DESIRE;
  return undefined;
}

function normalizeTemporal(value: unknown): DcecTemporalOperatorValue | undefined {
  const raw = String(value).toLowerCase();
  if (raw === DcecTemporalOperator.ALWAYS) return DcecTemporalOperator.ALWAYS;
  if (raw === DcecTemporalOperator.EVENTUALLY) return DcecTemporalOperator.EVENTUALLY;
  if (raw === DcecTemporalOperator.NEXT) return DcecTemporalOperator.NEXT;
  if (raw === DcecTemporalOperator.UNTIL) return DcecTemporalOperator.UNTIL;
  return undefined;
}

function toSemanticArray(value: unknown): DcecEnglishSemanticRecord[] {
  return Array.isArray(value) ? value.filter(isSemanticRecord) : [];
}

function nameFromSemantic(value: unknown): string | undefined {
  if (!isSemanticRecord(value)) return undefined;
  return stringName(value.name ?? value.word);
}

function stringName(value: unknown): string | undefined {
  if (typeof value === 'string' && value.length > 0) return value;
  if (isSemanticRecord(value) && typeof value.name === 'string') return value.name;
  return undefined;
}

function isSemanticRecord(value: unknown): value is DcecEnglishSemanticRecord {
  return typeof value === 'object' && value !== null && 'type' in value;
}

function termName(term: DcecTerm): string {
  if (term instanceof DcecVariableTerm) return term.variable.name;
  return term.toString();
}
