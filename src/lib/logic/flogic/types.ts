export type FLogicStatus = 'success' | 'failure' | 'unknown' | 'error';

export interface FLogicFrame {
  objectId: string;
  scalarMethods: Record<string, string>;
  setMethods: Record<string, Array<string>>;
  isa?: string;
  isaset: Array<string>;
}

export interface FLogicClass {
  classId: string;
  superclasses: Array<string>;
  signatureMethods: Record<string, string>;
}

export interface FLogicQuery {
  goal: string;
  bindings: Array<Record<string, string>>;
  status: FLogicStatus;
  errorMessage?: string;
}

export interface FLogicOntology {
  name: string;
  frames: Array<FLogicFrame>;
  classes: Array<FLogicClass>;
  rules: Array<string>;
  warnings: Array<string>;
}

export interface FLogicDisplayRow {
  objectId: string;
  label: string;
  className?: string;
  attributes: Array<{ name: string; value: string }>;
}

export const FLOGIC_TYPES_METADATA = {
  sourcePythonModule: 'logic/flogic/flogic_types.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'frame_class_query_ontology_shapes',
    'python_style_dict_serialization',
    'isa_isaset_normalization',
    'ontology_validation',
  ],
};

export interface PythonFLogicFrame {
  object_id: string;
  scalar_methods: Record<string, string>;
  set_methods: Record<string, Array<string>>;
  isa?: string;
  isaset: Array<string>;
}
export interface PythonFLogicClass {
  class_id: string;
  superclasses: Array<string>;
  signature_methods: Record<string, string>;
}
export interface PythonFLogicQuery {
  goal: string;
  bindings: Array<Record<string, string>>;
  status: FLogicStatus;
  error_message?: string;
}
export interface PythonFLogicOntology {
  name: string;
  frames: Array<PythonFLogicFrame>;
  classes: Array<PythonFLogicClass>;
  rules: Array<string>;
  warnings: Array<string>;
}
export interface FLogicValidationResult {
  valid: boolean;
  errors: Array<string>;
  warnings: Array<string>;
}

export function createFLogicFrame(input: {
  objectId: string;
  scalarMethods?: Record<string, string>;
  setMethods?: Record<string, Array<string>>;
  isa?: string;
  isaset?: Array<string>;
}): FLogicFrame {
  const isaset = [...(input.isaset ?? [])];
  if (input.isa && !isaset.includes(input.isa)) {
    isaset.unshift(input.isa);
  }
  return {
    objectId: input.objectId,
    scalarMethods: { ...(input.scalarMethods ?? {}) },
    setMethods: cloneSetMethods(input.setMethods ?? {}),
    isa: input.isa,
    isaset,
  };
}

export function createFLogicClass(input: {
  classId: string;
  superclasses?: Array<string>;
  signatureMethods?: Record<string, string>;
}): FLogicClass {
  return {
    classId: input.classId,
    superclasses: [...(input.superclasses ?? [])],
    signatureMethods: { ...(input.signatureMethods ?? {}) },
  };
}

export function createFLogicQuery(input: {
  goal: string;
  bindings?: Array<Record<string, string>>;
  status?: FLogicStatus;
  errorMessage?: string;
}): FLogicQuery {
  return {
    goal: input.goal,
    bindings: (input.bindings ?? []).map((binding) => ({ ...binding })),
    status: input.status ?? 'unknown',
    errorMessage: input.errorMessage,
  };
}

export function createFLogicOntology(
  input: {
    name?: string;
    frames?: Array<FLogicFrame>;
    classes?: Array<FLogicClass>;
    rules?: Array<string>;
    warnings?: Array<string>;
  } = {},
): FLogicOntology {
  return {
    name: input.name ?? 'F-logic ontology',
    frames: (input.frames ?? []).map((frame) => createFLogicFrame(frame)),
    classes: (input.classes ?? []).map((cls) => createFLogicClass(cls)),
    rules: [...(input.rules ?? [])],
    warnings: [...(input.warnings ?? [])],
  };
}

export function flogicQueryToDict(query: FLogicQuery): PythonFLogicQuery {
  return {
    goal: query.goal,
    bindings: query.bindings.map((binding) => ({ ...binding })),
    status: query.status,
    error_message: query.errorMessage,
  };
}

export function flogicQueryFromDict(query: PythonFLogicQuery): FLogicQuery {
  return createFLogicQuery({
    goal: query.goal,
    bindings: query.bindings,
    status: query.status,
    errorMessage: query.error_message,
  });
}

export function flogicOntologyToDict(ontology: FLogicOntology): PythonFLogicOntology {
  return {
    name: ontology.name,
    frames: ontology.frames.map((frame) => ({
      object_id: frame.objectId,
      scalar_methods: { ...frame.scalarMethods },
      set_methods: cloneSetMethods(frame.setMethods),
      isa: frame.isa,
      isaset: [...frame.isaset],
    })),
    classes: ontology.classes.map((cls) => ({
      class_id: cls.classId,
      superclasses: [...cls.superclasses],
      signature_methods: { ...cls.signatureMethods },
    })),
    rules: [...ontology.rules],
    warnings: [...ontology.warnings],
  };
}

export function flogicOntologyFromDict(ontology: PythonFLogicOntology): FLogicOntology {
  return createFLogicOntology({
    name: ontology.name,
    frames: ontology.frames.map((frame) =>
      createFLogicFrame({
        objectId: frame.object_id,
        scalarMethods: frame.scalar_methods,
        setMethods: frame.set_methods,
        isa: frame.isa,
        isaset: frame.isaset,
      }),
    ),
    classes: ontology.classes.map((cls) =>
      createFLogicClass({
        classId: cls.class_id,
        superclasses: cls.superclasses,
        signatureMethods: cls.signature_methods,
      }),
    ),
    rules: ontology.rules,
    warnings: ontology.warnings,
  });
}

export function validateFLogicOntology(ontology: FLogicOntology): FLogicValidationResult {
  const errors: string[] = [];
  const warnings = [...ontology.warnings];
  const frameIds = new Set<string>();
  const classIds = new Set(ontology.classes.map((cls) => cls.classId));

  for (const frame of ontology.frames) {
    if (!frame.objectId.trim()) {
      errors.push('F-logic frame objectId must be non-empty');
    } else if (frameIds.has(frame.objectId)) {
      errors.push(`Duplicate F-logic frame objectId: ${frame.objectId}`);
    }
    frameIds.add(frame.objectId);

    if (frame.isa && !frame.isaset.includes(frame.isa))
      errors.push(`F-logic frame ${frame.objectId} isa must also appear in isaset`);
    if (frame.isa && !classIds.has(frame.isa))
      warnings.push(`F-logic frame ${frame.objectId} references undeclared class ${frame.isa}`);
  }

  for (const cls of ontology.classes) {
    if (!cls.classId.trim()) errors.push('F-logic class classId must be non-empty');
  }

  return { valid: errors.length === 0, errors, warnings };
}

function cloneSetMethods(methods: Record<string, Array<string>>): Record<string, Array<string>> {
  return Object.fromEntries(Object.entries(methods).map(([name, values]) => [name, [...values]]));
}
