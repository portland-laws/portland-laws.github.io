const BN254_FIELD_MODULUS = BigInt(
  '21888242871839275222246405745257275088548364400416034343698204186575808495617',
);

const TDFOL_V1_V2_ALPHA = BigInt(7);
const TDFOL_V1_V2_BETA = BigInt(13);

export function normalizeProofText(text: string): string {
  return text.normalize('NFD').trim().replace(/\s+/g, ' ');
}

export function canonicalizeTheorem(theorem: string): string {
  return normalizeProofText(theorem);
}

export function canonicalizeAxioms(axioms: string[]): string[] {
  return [...new Set(axioms.map(normalizeProofText))].sort();
}

export async function theoremHashHex(theorem: string): Promise<string> {
  return sha256Hex(canonicalizeTheorem(theorem));
}

export async function axiomsCommitmentHex(axioms: string[]): Promise<string> {
  const canonical = canonicalizeAxioms(axioms);
  return sha256Hex(JSON.stringify({ axiom_count: canonical.length, axioms: canonical }));
}

export async function sha256FieldInt(text: string): Promise<bigint> {
  const hex = await sha256Hex(text);
  return BigInt(`0x${hex}`) % BN254_FIELD_MODULUS;
}

export async function tdfolV1AxiomsCommitmentHexV2(axioms: string[]): Promise<string> {
  const canonical = canonicalizeAxioms(axioms);
  let acc = BigInt(0);
  let betaPow = BigInt(1);

  for (const axiom of canonical) {
    const parsed = parseTdfolV1Axiom(axiom);
    const antecedent = parsed.antecedent ? await sha256FieldInt(parsed.antecedent) : BigInt(0);
    const consequent = await sha256FieldInt(parsed.consequent);
    const term = (consequent + TDFOL_V1_V2_ALPHA * antecedent) % BN254_FIELD_MODULUS;
    acc = (acc + term * betaPow) % BN254_FIELD_MODULUS;
    betaPow = (betaPow * TDFOL_V1_V2_BETA) % BN254_FIELD_MODULUS;
  }

  return acc.toString(16).padStart(64, '0');
}

export function parseTdfolV1Axiom(axiom: string): { antecedent?: string; consequent: string } {
  const normalized = normalizeProofText(axiom);
  const parts = normalized.split(/\s*(?:->|→)\s*/);
  if (parts.length === 1) {
    return { consequent: parts[0] };
  }
  return {
    antecedent: parts.slice(0, -1).join(' -> '),
    consequent: parts[parts.length - 1],
  };
}

async function sha256Hex(text: string): Promise<string> {
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

export { BN254_FIELD_MODULUS };
