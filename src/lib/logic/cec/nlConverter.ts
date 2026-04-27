import {
  DcecAtomicFormula,
  DcecCognitiveFormula,
  DcecConnectiveFormula,
  DcecDeonticFormula,
  DcecFormula,
  DcecTemporalFormula,
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

export interface DcecNlConversionResult {
  english_text: string;
  dcec_formula?: DcecFormula;
  success: boolean;
  error_message?: string;
  confidence: number;
  parse_method: string;
}

type DeonticPattern = [RegExp, DcecDeonticOperatorValue];
type CognitivePattern = [RegExp, DcecCognitiveOperatorValue];
type TemporalPattern = [RegExp, DcecTemporalOperatorValue];
type ConnectivePattern = [RegExp, DcecLogicalConnectiveValue];

export class DcecPatternMatcher {
  readonly namespace: DcecNamespace;
  readonly deonticPatterns: DeonticPattern[];
  readonly cognitivePatterns: CognitivePattern[];
  readonly temporalPatterns: TemporalPattern[];
  readonly connectivePatterns: ConnectivePattern[];

  constructor(namespace: DcecNamespace) {
    this.namespace = namespace;
    this.deonticPatterns = [
      [/(?:must not|should not|forbidden to|prohibited from) ([\w ]+)/, DcecDeonticOperator.PROHIBITION],
      [/(?:must|should|ought to|required to|obligated to) ([\w ]+)/, DcecDeonticOperator.OBLIGATION],
      [/(?:may|can|allowed to|permitted to) ([\w ]+)/, DcecDeonticOperator.PERMISSION],
    ];
    this.cognitivePatterns = [
      [/(?:believes that|thinks that) (.+)/, DcecCognitiveOperator.BELIEF],
      [/(?:knows that) (.+)/, DcecCognitiveOperator.KNOWLEDGE],
      [/(?:intends to|plans to) ([\w ]+)/, DcecCognitiveOperator.INTENTION],
      [/(?:desires to|wants to) ([\w ]+)/, DcecCognitiveOperator.DESIRE],
      [/(?:has goal to|aims to) ([\w ]+)/, DcecCognitiveOperator.GOAL],
    ];
    this.temporalPatterns = [
      [/always (.+)/, DcecTemporalOperator.ALWAYS],
      [/eventually (.+)/, DcecTemporalOperator.EVENTUALLY],
      [/next (.+)/, DcecTemporalOperator.NEXT],
    ];
    this.connectivePatterns = [
      [/(.+) and (.+)/, DcecLogicalConnective.AND],
      [/(.+) or (.+)/, DcecLogicalConnective.OR],
      [/if (.+) then (.+)/, DcecLogicalConnective.IMPLIES],
      [/not (.+)/, DcecLogicalConnective.NOT],
    ];
  }

  convert(text: string): DcecFormula {
    const normalized = normalizeEnglish(text);
    const agentName = this.extractAgent(normalized);

    for (const [pattern, operator] of this.cognitivePatterns) {
      const match = normalized.match(pattern);
      if (!match) continue;
      const content = match[1];
      const agent = this.createAgentTerm(agentName);
      const inner = this.convertOrAtomic(content, agentName);
      return new DcecCognitiveFormula(operator, agent, inner);
    }

    for (const [pattern, operator] of this.temporalPatterns) {
      const match = normalized.match(pattern);
      if (!match) continue;
      return new DcecTemporalFormula(operator, this.convert(match[1]));
    }

    for (const [pattern, connective] of this.connectivePatterns) {
      if (connective === DcecLogicalConnective.NOT) continue;
      const match = normalized.match(pattern);
      if (!match) continue;
      return new DcecConnectiveFormula(connective, [this.convert(match[1]), this.convert(match[2])]);
    }

    if (normalized.startsWith('not ')) {
      return new DcecConnectiveFormula(DcecLogicalConnective.NOT, [this.convert(normalized.slice(4))]);
    }

    for (const [pattern, operator] of this.deonticPatterns) {
      const match = normalized.match(pattern);
      if (!match) continue;
      const action = match[1];
      const predicate = this.createSimplePredicate(action);
      const agent = this.createAgentTerm(agentName);
      return new DcecDeonticFormula(operator, new DcecAtomicFormula(predicate, [agent]));
    }

    const predicate = this.createSimplePredicate(normalized);
    return new DcecAtomicFormula(predicate, [this.createAgentTerm(agentName)]);
  }

  extractAgent(text: string): string | undefined {
    const match = text.match(/^(?:the )?(\w+)/);
    return match?.[1];
  }

  createSimplePredicate(action: string): DcecPredicateSymbol {
    const name = action.trim().replace(/\s+/g, '_');
    return this.namespace.getPredicate(name)
      ?? this.namespace.addPredicate(name, ['Agent']);
  }

  createAgentTerm(agentName?: string): DcecVariableTerm {
    const name = agentName?.trim() || 'agent';
    const variable = this.namespace.getVariable(name)
      ?? this.namespace.addVariable(name, 'Agent');
    return new DcecVariableTerm(variable);
  }

  private convertOrAtomic(content: string, agentName?: string): DcecFormula {
    try {
      return this.convert(content);
    } catch {
      const agent = this.createAgentTerm(agentName);
      return new DcecAtomicFormula(this.createSimplePredicate(content), [agent]);
    }
  }
}

export class DcecNaturalLanguageConverter {
  readonly namespace: DcecNamespace;
  readonly matcher: DcecPatternMatcher;
  readonly conversionHistory: DcecNlConversionResult[] = [];
  private initialized = true;
  useGrammar = false;
  grammar: unknown = undefined;

  constructor(namespace = new DcecNamespace()) {
    this.namespace = namespace;
    this.matcher = new DcecPatternMatcher(this.namespace);
  }

  initialize(): boolean {
    this.initialized = true;
    return this.initialized;
  }

  convertToDcec(text: string): DcecNlConversionResult {
    try {
      const formula = this.matcher.convert(text);
      const result: DcecNlConversionResult = {
        english_text: text,
        dcec_formula: formula,
        success: true,
        confidence: 0.7,
        parse_method: 'pattern_matching',
      };
      this.conversionHistory.push(result);
      return result;
    } catch (error) {
      const result: DcecNlConversionResult = {
        english_text: text,
        success: false,
        error_message: error instanceof Error ? error.message : String(error),
        confidence: 0,
        parse_method: 'pattern_matching',
      };
      this.conversionHistory.push(result);
      return result;
    }
  }

  convertFromDcec(formula: DcecFormula): string {
    if (formula instanceof DcecDeonticFormula) {
      const inner = this.convertFromDcec(formula.formula);
      if (formula.operator === DcecDeonticOperator.OBLIGATION) return `must ${inner}`;
      if (formula.operator === DcecDeonticOperator.PERMISSION) return `may ${inner}`;
      if (formula.operator === DcecDeonticOperator.PROHIBITION) return `must not ${inner}`;
      return `${formula.operator}(${inner})`;
    }
    if (formula instanceof DcecCognitiveFormula) {
      const inner = this.convertFromDcec(formula.formula);
      if (formula.operator === DcecCognitiveOperator.BELIEF) return `${formula.agent} believes that ${inner}`;
      if (formula.operator === DcecCognitiveOperator.KNOWLEDGE) return `${formula.agent} knows that ${inner}`;
      if (formula.operator === DcecCognitiveOperator.INTENTION) return `${formula.agent} intends to ${inner}`;
      return `${formula.operator}(${formula.agent}, ${inner})`;
    }
    if (formula instanceof DcecTemporalFormula) {
      const inner = this.convertFromDcec(formula.formula);
      if (formula.operator === DcecTemporalOperator.ALWAYS) return `always ${inner}`;
      if (formula.operator === DcecTemporalOperator.EVENTUALLY) return `eventually ${inner}`;
      if (formula.operator === DcecTemporalOperator.NEXT) return `next ${inner}`;
      return `${formula.operator}(${inner})`;
    }
    if (formula instanceof DcecConnectiveFormula) {
      if (formula.connective === DcecLogicalConnective.NOT) return `not ${this.convertFromDcec(formula.formulas[0])}`;
      if (formula.connective === DcecLogicalConnective.AND) return formula.formulas.map((part) => this.convertFromDcec(part)).join(' and ');
      if (formula.connective === DcecLogicalConnective.OR) return formula.formulas.map((part) => this.convertFromDcec(part)).join(' or ');
      if (formula.connective === DcecLogicalConnective.IMPLIES) {
        return `if ${this.convertFromDcec(formula.formulas[0])} then ${this.convertFromDcec(formula.formulas[1])}`;
      }
      return formula.toString();
    }
    if (formula instanceof DcecAtomicFormula) {
      return formula.predicate.name.replace(/_/g, ' ');
    }
    return formula.toString();
  }

  getConversionStatistics(): Record<string, number> {
    if (this.conversionHistory.length === 0) return { total_conversions: 0 };
    const successful = this.conversionHistory.filter((result) => result.success).length;
    return {
      total_conversions: this.conversionHistory.length,
      successful,
      failed: this.conversionHistory.length - successful,
      success_rate: successful / this.conversionHistory.length,
      average_confidence: this.conversionHistory.reduce((sum, result) => sum + result.confidence, 0) / this.conversionHistory.length,
    };
  }

  toString(): string {
    return `NaturalLanguageConverter(conversions=${this.conversionHistory.length})`;
  }
}

export function createEnhancedDcecNlConverter(useGrammar = true): DcecNaturalLanguageConverter {
  const converter = new DcecNaturalLanguageConverter();
  converter.useGrammar = false;
  converter.grammar = undefined;
  if (useGrammar) {
    converter.useGrammar = false;
  }
  return converter;
}

export function parseDcecWithGrammar(_text: string): DcecFormula | undefined {
  return undefined;
}

export function linearizeDcecWithGrammar(_formula: DcecFormula): string | undefined {
  return undefined;
}

function normalizeEnglish(text: string): string {
  return text.trim().toLowerCase().replace(/\s+/g, ' ');
}
