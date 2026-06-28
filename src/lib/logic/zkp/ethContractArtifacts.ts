export type ContractAbiEntry = Record<string, unknown>;

export interface ContractArtifact {
  abi: ContractAbiEntry[];
  bytecode?: string;
  deployedBytecode?: string;
  contractName?: string;
}

export interface ContractArtifactDict {
  abi: ContractAbiEntry[];
  bytecode?: string;
  deployed_bytecode?: string;
  contract_name?: string;
}

export interface ContractArtifactOptions {
  contractName?: string;
}

type JsonRecord = Record<string, unknown>;

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function normalizeHexPrefixed(hexStr: string | null | undefined): string | undefined {
  if (hexStr === null || hexStr === undefined) {
    return undefined;
  }
  const normalized = String(hexStr).trim();
  if (normalized === '' || normalized.toLowerCase() === '0x') {
    return undefined;
  }
  if (normalized.startsWith('0x') || normalized.startsWith('0X')) {
    return `0x${normalized.slice(2)}`;
  }
  return `0x${normalized}`;
}

export function normalize_hex_prefixed(hexStr: string | null | undefined): string | undefined {
  return normalizeHexPrefixed(hexStr);
}

function parseArtifactInput(input: string | JsonRecord): JsonRecord {
  if (typeof input === 'string') {
    let parsed: unknown;
    try {
      parsed = JSON.parse(input);
    } catch (error) {
      throw new Error(`Contract artifact JSON could not be parsed: ${(error as Error).message}`);
    }
    if (!isRecord(parsed)) {
      throw new Error('Contract artifact JSON must be an object');
    }
    return parsed;
  }
  if (!isRecord(input)) {
    throw new Error('Contract artifact JSON must be an object');
  }
  return input;
}

function extractContractName(obj: JsonRecord, fallbackName?: string): string | undefined {
  for (const key of ['contractName', 'contract_name', 'name']) {
    const value = obj[key];
    if (typeof value === 'string' && value.trim() !== '') {
      return value.trim();
    }
  }
  return fallbackName;
}

function extractHexObject(value: unknown): string | undefined {
  if (typeof value === 'string') {
    return value;
  }
  if (isRecord(value) && typeof value.object === 'string') {
    return value.object;
  }
  return undefined;
}

function extractBytecode(
  obj: JsonRecord,
  key: 'bytecode' | 'deployedBytecode',
): string | undefined {
  const topLevelBytecode = obj[key];
  const topLevelHex = extractHexObject(topLevelBytecode);
  if (topLevelHex !== undefined) {
    return topLevelHex;
  }
  if (key === 'deployedBytecode') {
    const snakeCase = extractHexObject(obj.deployed_bytecode);
    if (snakeCase !== undefined) {
      return snakeCase;
    }
  }

  const evm = obj.evm;
  if (isRecord(evm)) {
    const evmBytecode = evm[key];
    const evmHex = extractHexObject(evmBytecode);
    if (evmHex !== undefined) {
      return evmHex;
    }
  }
  return undefined;
}

interface SelectedArtifact {
  artifact: JsonRecord;
  fallbackName?: string;
}

function artifactMatchesName(
  artifact: JsonRecord,
  fallbackName: string,
  expectedName: string,
): boolean {
  const candidates = [fallbackName, artifact.contractName, artifact.contract_name, artifact.name];
  return candidates.some(
    (candidate) => typeof candidate === 'string' && candidate.trim() === expectedName,
  );
}

function selectCompiledArtifact(
  obj: JsonRecord,
  options: ContractArtifactOptions = {},
): SelectedArtifact {
  if (Array.isArray(obj.abi)) {
    return { artifact: obj };
  }

  const contracts = obj.contracts;
  if (!isRecord(contracts)) {
    return { artifact: obj };
  }

  const candidates: SelectedArtifact[] = [];
  for (const [sourceName, sourceValue] of Object.entries(contracts)) {
    if (isRecord(sourceValue) && Array.isArray(sourceValue.abi)) {
      candidates.push({ artifact: sourceValue, fallbackName: sourceName });
      continue;
    }
    if (!isRecord(sourceValue)) {
      continue;
    }
    for (const [contractName, artifact] of Object.entries(sourceValue)) {
      if (isRecord(artifact) && Array.isArray(artifact.abi)) {
        candidates.push({ artifact, fallbackName: contractName });
      }
    }
  }

  if (options.contractName !== undefined) {
    const expectedName = options.contractName.trim();
    const selected = candidates.find((candidate) =>
      artifactMatchesName(candidate.artifact, candidate.fallbackName ?? '', expectedName),
    );
    if (selected === undefined) {
      throw new Error(`Contract artifact '${expectedName}' was not found in compiled contracts`);
    }
    return selected;
  }

  if (candidates.length === 1) {
    return candidates[0];
  }
  if (candidates.length > 1) {
    throw new Error(
      'Contract artifact contains multiple compiled contracts; pass contractName to select one',
    );
  }
  return { artifact: obj };
}

function normalizeAbi(abi: unknown): ContractAbiEntry[] {
  if (!Array.isArray(abi)) {
    throw new Error("Contract artifact missing 'abi' list");
  }
  return abi.map((entry) => {
    if (!isRecord(entry)) {
      throw new Error('Contract ABI entries must be JSON objects');
    }
    return { ...entry };
  });
}

export function loadContractArtifactFromJson(
  input: string | JsonRecord,
  options: ContractArtifactOptions = {},
): ContractArtifact {
  const selected = selectCompiledArtifact(parseArtifactInput(input), options);
  const obj = selected.artifact;
  const bytecode = normalizeHexPrefixed(extractBytecode(obj, 'bytecode'));
  const deployedBytecode = normalizeHexPrefixed(extractBytecode(obj, 'deployedBytecode'));
  const contractName = extractContractName(obj, selected.fallbackName);

  return {
    abi: normalizeAbi(obj.abi),
    ...(bytecode === undefined ? {} : { bytecode }),
    ...(deployedBytecode === undefined ? {} : { deployedBytecode }),
    ...(contractName === undefined ? {} : { contractName }),
  };
}

export function load_contract_artifact_from_json(
  input: string | JsonRecord,
  options: ContractArtifactOptions = {},
): ContractArtifactDict {
  const artifact = loadContractArtifactFromJson(input, options);
  return {
    abi: artifact.abi,
    ...(artifact.bytecode === undefined ? {} : { bytecode: artifact.bytecode }),
    ...(artifact.deployedBytecode === undefined
      ? {}
      : { deployed_bytecode: artifact.deployedBytecode }),
    ...(artifact.contractName === undefined ? {} : { contract_name: artifact.contractName }),
  };
}

export function loadContractAbiFromJson(
  input: string | JsonRecord,
  options: ContractArtifactOptions = {},
): ContractAbiEntry[] {
  return loadContractArtifactFromJson(input, options).abi;
}

export function load_contract_abi_from_json(
  input: string | JsonRecord,
  options: ContractArtifactOptions = {},
): ContractAbiEntry[] {
  return loadContractAbiFromJson(input, options);
}

export function loadContractArtifact(_path: string): never {
  throw new Error(
    'Filesystem artifact path loading is not browser-native; pass artifact JSON/object instead.',
  );
}

export function load_contract_artifact(path: string): never {
  return loadContractArtifact(path);
}

export function loadContractAbi(path: string): never {
  return loadContractArtifact(path);
}

export function load_contract_abi(path: string): never {
  return loadContractAbi(path);
}
