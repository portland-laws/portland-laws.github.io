const U64_MAX = (BigInt(1) << BigInt(64)) - BigInt(1);

export interface RegisterVKPayload {
  circuitIdBytes32: string;
  version: number | bigint;
  vkHashBytes32: string;
}

export interface RegisterVKPayloadDict {
  circuit_id_bytes32: string;
  version: number | bigint;
  vk_hash_bytes32: string;
}

export function normalizeHexNoPrefix(value: string): string {
  if (typeof value !== 'string') {
    throw new TypeError('value must be a str');
  }
  const normalized = value.trim().toLowerCase();
  return normalized.startsWith('0x') ? normalized.slice(2) : normalized;
}

export function normalizeBytes32Hex(value: string): string {
  const normalized = normalizeHexNoPrefix(value);
  if (normalized.length !== 64) {
    throw new Error('value must be 32 bytes (64 hex chars)');
  }
  if (!/^[0-9a-f]+$/.test(normalized)) {
    throw new Error('value must be hex');
  }
  return `0x${normalized}`;
}

export function normalize_bytes32_hex(value: string): string {
  return normalizeBytes32Hex(value);
}

export function vkHashHexToBytes32(vkHashHex: string): string {
  return normalizeBytes32Hex(vkHashHex);
}

export function vk_hash_hex_to_bytes32(vkHashHex: string): string {
  return vkHashHexToBytes32(vkHashHex);
}

export function circuitIdTextToBytes32(_circuitIdText: string): string {
  if (typeof _circuitIdText !== 'string') {
    throw new TypeError('circuit_id_text must be a str');
  }
  if (_circuitIdText === '') {
    throw new Error('circuit_id_text cannot be empty');
  }
  throw new Error('Keccak circuit_id_text hashing requires a browser-native keccak implementation; pass a precomputed bytes32 circuitId.');
}

export function circuit_id_text_to_bytes32(circuitIdText: string): string {
  return circuitIdTextToBytes32(circuitIdText);
}

export function buildRegisterVkPayload(options: {
  circuitIdBytes32: string;
  version: number | bigint;
  vkHashHex: string;
}): RegisterVKPayload {
  if (typeof options.version !== 'number' && typeof options.version !== 'bigint') {
    throw new TypeError('version must be int');
  }
  if (typeof options.version === 'number' && !Number.isInteger(options.version)) {
    throw new TypeError('version must be int');
  }
  const version = BigInt(options.version);
  if (version < BigInt(0) || version > U64_MAX) {
    throw new Error('version must fit uint64');
  }
  return {
    circuitIdBytes32: normalizeBytes32Hex(options.circuitIdBytes32),
    version: options.version,
    vkHashBytes32: vkHashHexToBytes32(options.vkHashHex),
  };
}

export function build_register_vk_payload(options: {
  circuit_id_bytes32: string;
  version: number | bigint;
  vk_hash_hex: string;
}): RegisterVKPayloadDict {
  const payload = buildRegisterVkPayload({
    circuitIdBytes32: options.circuit_id_bytes32,
    version: options.version,
    vkHashHex: options.vk_hash_hex,
  });
  return {
    circuit_id_bytes32: payload.circuitIdBytes32,
    version: payload.version,
    vk_hash_bytes32: payload.vkHashBytes32,
  };
}

export function buildRegisterVkCalldata(_options: { payload: RegisterVKPayload; overwrite?: boolean }): string {
  if (_options.overwrite !== undefined && typeof _options.overwrite !== 'boolean') {
    throw new TypeError('overwrite must be bool');
  }
  throw new Error('ABI calldata encoding requires a browser-native ABI/keccak implementation and is not yet ported.');
}

export function build_register_vk_calldata(options: {
  payload: RegisterVKPayloadDict;
  overwrite?: boolean;
}): string {
  return buildRegisterVkCalldata({
    overwrite: options.overwrite,
    payload: {
      circuitIdBytes32: options.payload.circuit_id_bytes32,
      version: options.payload.version,
      vkHashBytes32: options.payload.vk_hash_bytes32,
    },
  });
}
