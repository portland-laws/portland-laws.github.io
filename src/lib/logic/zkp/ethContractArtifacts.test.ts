import {
  loadContractAbi,
  loadContractAbiFromJson,
  loadContractArtifact,
  loadContractArtifactFromJson,
  load_contract_artifact_from_json,
  normalizeHexPrefixed,
} from './ethContractArtifacts';

describe('EVM contract artifact helpers', () => {
  const abi = [
    {
      inputs: [{ internalType: 'bytes32', name: 'vkHash', type: 'bytes32' }],
      name: 'getVK',
      outputs: [{ internalType: 'bool', name: '', type: 'bool' }],
      stateMutability: 'view',
      type: 'function',
    },
  ];

  it('normalizes optional bytecode values with Python-compatible prefix behavior', () => {
    expect(normalizeHexPrefixed(undefined)).toBeUndefined();
    expect(normalizeHexPrefixed(null)).toBeUndefined();
    expect(normalizeHexPrefixed('')).toBeUndefined();
    expect(normalizeHexPrefixed('0x')).toBeUndefined();
    expect(normalizeHexPrefixed('abc123')).toBe('0xabc123');
    expect(normalizeHexPrefixed('0XABC123')).toBe('0xABC123');
  });

  it('loads top-level Hardhat/Truffle artifact objects', () => {
    expect(loadContractArtifactFromJson({ abi, bytecode: '0x6000', contractName: 'VKRegistry' })).toEqual({
      abi,
      bytecode: '0x6000',
      contractName: 'VKRegistry',
    });
  });

  it('loads bytecode object and snake-case contract names', () => {
    expect(loadContractArtifactFromJson({ abi, bytecode: { object: '6001' }, contract_name: 'Verifier' })).toEqual({
      abi,
      bytecode: '0x6001',
      contractName: 'Verifier',
    });
  });

  it('loads solc-style evm bytecode from JSON strings', () => {
    const artifactJson = JSON.stringify({
      abi,
      evm: { bytecode: { object: '0x6002' } },
      name: 'Groth16Verifier',
    });

    expect(loadContractArtifactFromJson(artifactJson)).toEqual({
      abi,
      bytecode: '0x6002',
      contractName: 'Groth16Verifier',
    });
    expect(loadContractAbiFromJson(artifactJson)).toEqual(abi);
  });

  it('returns Python-style dictionary fields through snake-case aliases', () => {
    expect(load_contract_artifact_from_json({ abi, bytecode: '6003', contractName: 'Registry' })).toEqual({
      abi,
      bytecode: '0x6003',
      contract_name: 'Registry',
    });
  });

  it('omits empty bytecode and contract names', () => {
    expect(loadContractArtifactFromJson({ abi, bytecode: '0x', contractName: '   ' })).toEqual({ abi });
  });

  it('validates artifact and ABI shape', () => {
    expect(() => loadContractArtifactFromJson('[]')).toThrow('must be an object');
    expect(() => loadContractArtifactFromJson({ bytecode: '6000' })).toThrow("missing 'abi' list");
    expect(() => loadContractArtifactFromJson({ abi: ['not-object'] })).toThrow('ABI entries');
    expect(() => loadContractArtifactFromJson('{')).toThrow('could not be parsed');
  });

  it('fails closed for filesystem path helpers in the browser port', () => {
    expect(() => loadContractArtifact('./Verifier.json')).toThrow('Filesystem artifact path loading is not browser-native');
    expect(() => loadContractAbi('./Verifier.json')).toThrow('Filesystem artifact path loading is not browser-native');
  });
});
