import { objectIdToPortlandIdentifier } from '../normalization';
import type { FLogicClass, FLogicDisplayRow, FLogicFrame, FLogicOntology } from './types';

export function formatFLogicFrame(frame: FLogicFrame): string {
  const scalar = Object.entries(frame.scalarMethods).map(([name, value]) => `${name} -> ${quoteIfNeeded(value)}`);
  const sets = Object.entries(frame.setMethods).map(
    ([name, values]) => `${name} ->> {${values.map(quoteIfNeeded).join(',')}}`,
  );
  const attrs = [...scalar, ...sets].join(', ');
  const base = attrs ? `${frame.objectId}[${attrs}]` : frame.objectId;
  return frame.isa ? `${base} : ${frame.isa}` : base;
}

export function formatFLogicClass(cls: FLogicClass): string {
  const hierarchy = cls.superclasses.map((superclass) => `${cls.classId} :: ${superclass}.`);
  const signatures = Object.entries(cls.signatureMethods).map(([name, type]) => `${cls.classId}[${name} => ${type}].`);
  return [...hierarchy, ...signatures].join('\n');
}

export function formatFLogicOntology(ontology: FLogicOntology): string {
  return [
    ...ontology.classes.map(formatFLogicClass).filter(Boolean),
    ...ontology.frames.map((frame) => `${formatFLogicFrame(frame)}.`),
    ...ontology.rules,
  ].join('\n');
}

export function frameToDisplayRow(frame: FLogicFrame): FLogicDisplayRow {
  const citation = objectIdToPortlandIdentifier(frame.objectId);
  return {
    objectId: frame.objectId,
    label: frame.scalarMethods.identifier || citation || frame.objectId,
    className: frame.isa,
    attributes: [
      ...Object.entries(frame.scalarMethods).map(([name, value]) => ({ name, value })),
      ...Object.entries(frame.setMethods).map(([name, values]) => ({ name, value: values.join(', ') })),
    ],
  };
}

function quoteIfNeeded(value: string): string {
  if (/^[A-Za-z_][A-Za-z0-9_?]*$/.test(value)) {
    return value;
  }
  return `"${value.replace(/"/g, '\\"')}"`;
}

