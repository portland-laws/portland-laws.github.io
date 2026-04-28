const ATOM_PATTERN = /^[A-Za-z][A-Za-z0-9_]*$/;

export class LegalTheoremSyntaxError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'LegalTheoremSyntaxError';
  }
}

export interface HornAxiom {
  antecedent?: string;
  consequent: string;
}

export function parseTdfolV1Atom(atom: string, label: string): string {
  const trimmed = String(atom).trim();
  if (!trimmed || !ATOM_PATTERN.test(trimmed)) {
    throw new LegalTheoremSyntaxError(`${label} must be an atom matching [A-Za-z][A-Za-z0-9_]*`);
  }
  return trimmed;
}

export function parseTdfolV1HornAxiom(text: string): HornAxiom {
  if (text === null || text === undefined) {
    throw new LegalTheoremSyntaxError('axiom must be a string');
  }
  const source = String(text).trim();
  if (!source) {
    throw new LegalTheoremSyntaxError('axiom cannot be empty');
  }

  if (source.includes('->')) {
    const parts = source.split('->');
    if (parts.length !== 2) {
      throw new LegalTheoremSyntaxError("axiom may contain at most one '->'");
    }
    return {
      antecedent: parseTdfolV1Atom(parts[0], 'axiom antecedent'),
      consequent: parseTdfolV1Atom(parts[1], 'axiom consequent'),
    };
  }

  return { consequent: parseTdfolV1Atom(source, 'axiom') };
}

export function parse_tdfol_v1_axiom(text: string): HornAxiom {
  return parseTdfolV1HornAxiom(text);
}

export function parseTdfolV1Theorem(text: string): string {
  if (text === null || text === undefined) {
    throw new LegalTheoremSyntaxError('theorem must be a string');
  }
  return parseTdfolV1Atom(String(text), 'theorem');
}

export function parse_tdfol_v1_theorem(text: string): string {
  return parseTdfolV1Theorem(text);
}

export function evaluateTdfolV1Holds(privateAxioms: Iterable<string>, theorem: string): boolean {
  const axioms = [...privateAxioms].map(parseTdfolV1HornAxiom);
  const goal = parseTdfolV1Theorem(theorem);
  const known = new Set(axioms.filter((axiom) => !axiom.antecedent).map((axiom) => axiom.consequent));
  const implications = axioms.filter((axiom) => axiom.antecedent);

  let changed = true;
  while (changed) {
    changed = false;
    for (const axiom of implications) {
      if (axiom.antecedent && known.has(axiom.antecedent) && !known.has(axiom.consequent)) {
        known.add(axiom.consequent);
        changed = true;
      }
    }
  }

  return known.has(goal);
}

export function evaluate_tdfol_v1_holds(privateAxioms: Iterable<string>, theorem: string): boolean {
  return evaluateTdfolV1Holds(privateAxioms, theorem);
}

export function deriveTdfolV1Trace(privateAxioms: Iterable<string>, theorem: string): string[] | undefined {
  const axioms = [...privateAxioms].map(parseTdfolV1HornAxiom);
  const goal = parseTdfolV1Theorem(theorem);
  const facts = [...new Set(axioms.filter((axiom) => !axiom.antecedent).map((axiom) => axiom.consequent))].sort();
  const known = new Set(facts);
  const implications = axioms
    .filter((axiom) => axiom.antecedent)
    .sort((left, right) => `${left.antecedent ?? ''}\u0000${left.consequent}`.localeCompare(`${right.antecedent ?? ''}\u0000${right.consequent}`));
  const trace = [...facts];

  let changed = true;
  while (changed) {
    changed = false;
    for (const axiom of implications) {
      if (axiom.antecedent && known.has(axiom.antecedent) && !known.has(axiom.consequent)) {
        known.add(axiom.consequent);
        trace.push(axiom.consequent);
        changed = true;
      }
    }
  }

  return known.has(goal) ? trace : undefined;
}

export function derive_tdfol_v1_trace(privateAxioms: Iterable<string>, theorem: string): string[] | undefined {
  return deriveTdfolV1Trace(privateAxioms, theorem);
}
