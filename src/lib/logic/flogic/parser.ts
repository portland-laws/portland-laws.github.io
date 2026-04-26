import { normalizePredicateName } from '../normalization';
import type { FLogicClass, FLogicFrame, FLogicOntology } from './types';

export function parseFLogicOntology(source: string, name = 'F-logic ontology'): FLogicOntology {
  const ontology: FLogicOntology = {
    name,
    frames: [],
    classes: [],
    rules: [],
    warnings: [],
  };

  for (const statement of splitStatements(source)) {
    const trimmed = statement.trim();
    if (!trimmed) {
      continue;
    }

    if (trimmed.includes(':-')) {
      ontology.rules.push(`${trimmed}.`);
      continue;
    }

    const classMatch = trimmed.match(/^([A-Za-z_][A-Za-z0-9_]*)\s*::\s*([A-Za-z_][A-Za-z0-9_]*)$/);
    if (classMatch) {
      mergeClass(ontology.classes, {
        classId: classMatch[1],
        superclasses: [classMatch[2]],
        signatureMethods: {},
      });
      continue;
    }

    const frame = parseFLogicFrame(trimmed);
    if (frame) {
      ontology.frames.push(frame);
      continue;
    }

    ontology.warnings.push(`Unsupported F-logic statement: ${trimmed}`);
  }

  return ontology;
}

export function parseFLogicFrame(statement: string): FLogicFrame | null {
  const frameMatch = statement.match(
    /^([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[([\s\S]*)\])?\s*(?::\s*([A-Za-z_][A-Za-z0-9_]*))?$/,
  );
  if (!frameMatch) {
    return null;
  }

  const [, objectId, rawAttributes = '', isa] = frameMatch;
  const frame: FLogicFrame = {
    objectId,
    scalarMethods: {},
    setMethods: {},
    isa,
    isaset: isa ? [isa] : [],
  };

  for (const attribute of splitAttributes(rawAttributes)) {
    const setMatch = attribute.match(/^([A-Za-z_][A-Za-z0-9_]*)\s*->>\s*\{([\s\S]*)\}$/);
    if (setMatch) {
      frame.setMethods[normalizePredicateName(setMatch[1])] = splitSetValues(setMatch[2]);
      continue;
    }

    const scalarMatch = attribute.match(/^([A-Za-z_][A-Za-z0-9_]*)\s*->\s*([\s\S]+)$/);
    if (scalarMatch) {
      frame.scalarMethods[normalizePredicateName(scalarMatch[1])] = unquote(scalarMatch[2].trim());
    }
  }

  return frame;
}

export function normalizeFLogicGoal(goal: string): string {
  return goal.replace(/\b[A-Za-z_][A-Za-z0-9_]*\b/g, (token, offset, full) => {
    const previous = full[offset - 1];
    if (previous === '?' || token === ':-') {
      return token;
    }
    return normalizePredicateName(token);
  });
}

function splitStatements(source: string): string[] {
  const statements: string[] = [];
  let current = '';
  let inQuote = false;

  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    if (char === '"' && source[index - 1] !== '\\') {
      inQuote = !inQuote;
    }
    if (char === '.' && !inQuote) {
      statements.push(current);
      current = '';
    } else {
      current += char;
    }
  }

  if (current.trim()) {
    statements.push(current);
  }
  return statements;
}

function splitAttributes(source: string): string[] {
  const attributes: string[] = [];
  let current = '';
  let inQuote = false;
  let braceDepth = 0;

  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    if (char === '"' && source[index - 1] !== '\\') {
      inQuote = !inQuote;
    } else if (char === '{' && !inQuote) {
      braceDepth += 1;
    } else if (char === '}' && !inQuote) {
      braceDepth -= 1;
    }

    if (char === ',' && !inQuote && braceDepth === 0) {
      if (current.trim()) {
        attributes.push(current.trim());
      }
      current = '';
    } else {
      current += char;
    }
  }

  if (current.trim()) {
    attributes.push(current.trim());
  }
  return attributes;
}

function splitSetValues(source: string): string[] {
  return splitAttributes(source).map((value) => unquote(value.trim()));
}

function unquote(value: string): string {
  const trimmed = value.trim();
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
    return trimmed.slice(1, -1).replace(/\\"/g, '"');
  }
  return trimmed;
}

function mergeClass(classes: FLogicClass[], next: FLogicClass): void {
  const existing = classes.find((cls) => cls.classId === next.classId);
  if (!existing) {
    classes.push(next);
    return;
  }
  for (const superclass of next.superclasses) {
    if (!existing.superclasses.includes(superclass)) {
      existing.superclasses.push(superclass);
    }
  }
}

