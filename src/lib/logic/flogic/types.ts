export type FLogicStatus = 'success' | 'failure' | 'unknown' | 'error';

export interface FLogicFrame {
  objectId: string;
  scalarMethods: Record<string, string>;
  setMethods: Record<string, string[]>;
  isa?: string;
  isaset: string[];
}

export interface FLogicClass {
  classId: string;
  superclasses: string[];
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
  frames: FLogicFrame[];
  classes: FLogicClass[];
  rules: string[];
  warnings: string[];
}

export interface FLogicDisplayRow {
  objectId: string;
  label: string;
  className?: string;
  attributes: Array<{ name: string; value: string }>;
}

