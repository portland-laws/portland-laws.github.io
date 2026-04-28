export type ContractAbiEntry = Record<string, unknown>;

export interface ContractArtifact {
  abi: ContractAbiEntry[];
  bytecode?: string;
  contractName?: string;
}

export interface ContractArtifactDict {
  abi: ContractAbiEntry[];
  bytecode?: string;
  contract_name?: string;
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
  if (normalized === '' || normalized === '0x') {
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

function extractContractName(obj: JsonRecord): string | undefined {
  for (const key of ['contractName', 'contract_name', 'name']) {
    const value = obj[key];
    if (typeof value === 'string' && value.trim() !== '') {
      return value.trim();
    }
  }
  return undefined;
}

function extractBytecode(obj: JsonRecord): string | undefined {
  const topLevelBytecode = obj.bytecode;
  if (typeof topLevelBytecode === 'string') {
    return topLevelBytecode;
  }
  if (isRecord(topLevelBytecode) && typeof topLevelBytecode.object === 'string') {
    return topLevelBytecode.object;
  }

  const evm = obj.evm;
  if (isRecord(evm)) {
    const evmBytecode = evm.bytecode;
    if (isRecord(evmBytecode) && typeof evmBytecode.object === 'string') {
      return evmBytecode.object;
    }
  }
  return undefined;
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

export function loadContractArtifactFromJson(input: string | JsonRecord): ContractArtifact {
  const obj = parseArtifactInput(input);
  const bytecode = normalizeHexPrefixed(extractBytecode(obj));
  const contractName = extractContractName(obj);

  return {
    abi: normalizeAbi(obj.abi),
    ...(bytecode === undefined ? {} : { bytecode }),
    ...(contractName === undefined ? {} : { contractName }),
  };
}

export function load_contract_artifact_from_json(input: string | JsonRecord): ContractArtifactDict {
  const artifact = loadContractArtifactFromJson(input);
  return {
    abi: artifact.abi,
    ...(artifact.bytecode === undefined ? {} : { bytecode: artifact.bytecode }),
    ...(artifact.contractName === undefined ? {} : { contract_name: artifact.contractName }),
  };
}

export function loadContractAbiFromJson(input: string | JsonRecord): ContractAbiEntry[] {
  return loadContractArtifactFromJson(input).abi;
}

export function load_contract_abi_from_json(input: string | JsonRecord): ContractAbiEntry[] {
  return loadContractAbiFromJson(input);
}

export function loadContractArtifact(_path: string): never {
  throw new Error('Filesystem artifact path loading is not browser-native; pass artifact JSON/object instead.');
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
