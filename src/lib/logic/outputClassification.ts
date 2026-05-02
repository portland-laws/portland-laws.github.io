export const logicOutputKinds = [
  'simulated',
  'heuristic',
  'proof-checking',
  'cryptographic',
] as const;

export type LogicOutputKind = (typeof logicOutputKinds)[number];

export interface LogicOutputLanguage {
  readonly kind: LogicOutputKind;
  readonly uiLabel: string;
  readonly apiQualifier: string;
  readonly description: string;
  readonly cryptographic: boolean;
}

export interface LogicOutputMetadata extends LogicOutputLanguage {
  readonly warnings: readonly string[];
}

export type LogicOutputMetadataValidation =
  | { readonly ok: true; readonly metadata: LogicOutputMetadata }
  | { readonly ok: false; readonly reason: string; readonly warnings: readonly string[] };

type UnknownObject = { readonly [key: string]: unknown };

const LANGUAGE_BY_KIND: { readonly [Kind in LogicOutputKind]: LogicOutputLanguage } = {
  simulated: {
    kind: 'simulated',
    uiLabel: 'Simulated output',
    apiQualifier: 'simulated',
    description:
      'Produced by a deterministic browser-native simulation and not a proof or cryptographic verification.',
    cryptographic: false,
  },
  heuristic: {
    kind: 'heuristic',
    uiLabel: 'Heuristic output',
    apiQualifier: 'heuristic',
    description:
      'Produced by deterministic rules or ranking logic and not a proof or cryptographic verification.',
    cryptographic: false,
  },
  'proof-checking': {
    kind: 'proof-checking',
    uiLabel: 'Proof-checking output',
    apiQualifier: 'proof-checking',
    description:
      'Produced by local proof-checking logic; this does not imply cryptographic verification.',
    cryptographic: false,
  },
  cryptographic: {
    kind: 'cryptographic',
    uiLabel: 'Cryptographic output',
    apiQualifier: 'cryptographic',
    description:
      'Produced by an explicitly cryptographic browser-native implementation or compatible WASM verifier.',
    cryptographic: true,
  },
};

export function isLogicOutputKind(value: unknown): value is LogicOutputKind {
  return typeof value === 'string' && logicOutputKinds.includes(value as LogicOutputKind);
}

export function getLogicOutputLanguage(kind: LogicOutputKind): LogicOutputLanguage {
  return LANGUAGE_BY_KIND[kind];
}

export function getLogicOutputLanguageCatalog(): readonly LogicOutputLanguage[] {
  return logicOutputKinds.map((kind) => LANGUAGE_BY_KIND[kind]);
}

export function createLogicOutputMetadata(kind: LogicOutputKind): LogicOutputMetadata {
  return {
    ...LANGUAGE_BY_KIND[kind],
    warnings: warningsForKind(kind),
  };
}

export function validateLogicOutputMetadata(value: unknown): LogicOutputMetadataValidation {
  if (!isUnknownObject(value)) {
    return failClosed('metadata must be an object', []);
  }

  const { kind } = value;
  if (!isLogicOutputKind(kind)) {
    return failClosed(
      'metadata.kind must be one of simulated, heuristic, proof-checking, or cryptographic',
      ['Unrecognized output language is not promoted to a stronger guarantee.'],
    );
  }

  const expected = LANGUAGE_BY_KIND[kind];
  const mismatches = metadataMismatches(value, expected);
  if (mismatches.length > 0) {
    return failClosed('metadata language does not match the declared output kind', mismatches);
  }

  return { ok: true, metadata: createLogicOutputMetadata(kind) };
}

function isUnknownObject(value: unknown): value is UnknownObject {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function metadataMismatches(value: UnknownObject, expected: LogicOutputLanguage): string[] {
  const mismatches: string[] = [];

  if ('apiQualifier' in value && value.apiQualifier !== expected.apiQualifier) {
    mismatches.push(`apiQualifier must be ${expected.apiQualifier}`);
  }
  if ('uiLabel' in value && value.uiLabel !== expected.uiLabel) {
    mismatches.push(`uiLabel must be ${expected.uiLabel}`);
  }
  if ('cryptographic' in value && value.cryptographic !== expected.cryptographic) {
    mismatches.push(`cryptographic must be ${String(expected.cryptographic)}`);
  }

  return mismatches;
}

function warningsForKind(kind: LogicOutputKind): readonly string[] {
  if (kind === 'cryptographic') {
    return [
      'Use only when backed by an explicitly cryptographic browser-native or WASM implementation.',
    ];
  }
  if (kind === 'proof-checking') {
    return [
      'Proof-checking output must not be described as cryptographic unless a cryptographic verifier produced it.',
    ];
  }
  return ['This output is not proof-checking or cryptographic verification.'];
}

function failClosed(reason: string, warnings: readonly string[]): LogicOutputMetadataValidation {
  return { ok: false, reason, warnings };
}
