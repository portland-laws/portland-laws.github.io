import { formatFLogicOntology } from './formatter';
import type { FLogicClass, FLogicFrame, FLogicOntology, FLogicQuery } from './types';

export const ERGOAI_AVAILABLE = false;
export const ERGOAI_SUBMODULE_PATH = null;

export interface ErgoAIWrapperStatistics {
  ontologyName: string;
  frames: number;
  classes: number;
  rules: number;
  simulationMode: true;
  ergoaiBinary: null;
}

export interface ErgoAIWrapperOptions {
  ontologyName?: string;
  ontology?: FLogicOntology;
  unavailableMessage?: string;
}

const DEFAULT_UNAVAILABLE_MESSAGE =
  'ErgoAI binary unavailable in browser-native TypeScript runtime';

export class ErgoAIWrapper {
  ontology: FLogicOntology;
  readonly simulationMode = true;
  readonly binary = null;
  private readonly unavailableMessage: string;

  constructor(options: ErgoAIWrapperOptions | string = {}) {
    const normalizedOptions = typeof options === 'string' ? { ontologyName: options } : options;
    this.ontology = normalizedOptions.ontology ?? {
      name: normalizedOptions.ontologyName ?? 'default',
      frames: [],
      classes: [],
      rules: [],
      warnings: [],
    };
    this.unavailableMessage = normalizedOptions.unavailableMessage ?? DEFAULT_UNAVAILABLE_MESSAGE;
  }

  addFrame(frame: FLogicFrame): void {
    this.ontology.frames.push(frame);
  }

  addClass(cls: FLogicClass): void {
    this.ontology.classes.push(cls);
  }

  addRule(rule: string): void {
    this.ontology.rules.push(rule);
  }

  loadOntology(ontology: FLogicOntology): void {
    this.ontology = ontology;
  }

  query(goal: string): FLogicQuery {
    return {
      goal,
      bindings: [],
      status: 'unknown',
      errorMessage: this.unavailableMessage,
    };
  }

  batchQuery(goals: readonly string[]): FLogicQuery[] {
    return goals.map((goal) => this.query(goal));
  }

  buildErgoProgram(extraGoal: string): string {
    return `${this.getProgram()}\n\n?- ${extraGoal}.`;
  }

  getProgram(): string {
    return formatFLogicOntology(this.ontology);
  }

  getStatistics(): ErgoAIWrapperStatistics {
    return {
      ontologyName: this.ontology.name,
      frames: this.ontology.frames.length,
      classes: this.ontology.classes.length,
      rules: this.ontology.rules.length,
      simulationMode: true,
      ergoaiBinary: null,
    };
  }
}

export function parseErgoOutput(output: string): Array<Record<string, string>> {
  const bindings: Array<Record<string, string>> = [];
  for (const rawLine of output.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('%')) {
      continue;
    }
    const binding: Record<string, string> = {};
    for (const rawPart of line.split(',')) {
      const separatorIndex = rawPart.indexOf('=');
      if (separatorIndex < 0) {
        continue;
      }
      const variable = rawPart.slice(0, separatorIndex).trim();
      const value = rawPart.slice(separatorIndex + 1).trim();
      if (variable) {
        binding[variable] = value;
      }
    }
    if (Object.keys(binding).length > 0) {
      bindings.push(binding);
    }
  }
  return bindings;
}
