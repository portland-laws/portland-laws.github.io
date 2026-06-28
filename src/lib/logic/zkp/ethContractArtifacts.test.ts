import {
  loadContractAbi,
  loadContractAbiFromJson,
  loadContractArtifact,
  loadContractArtifactFromJson,
  load_contract_artifact_from_json,
  load_contract_abi_from_json,
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
    expect(
      loadContractArtifactFromJson({ abi, bytecode: '0x6000', contractName: 'VKRegistry' }),
    ).toEqual({
      abi,
      bytecode: '0x6000',
      contractName: 'VKRegistry',
    });
  });

  it('loads bytecode object and snake-case contract names', () => {
    expect(
      loadContractArtifactFromJson({
        abi,
        bytecode: { object: '6001' },
        contract_name: 'Verifier',
      }),
    ).toEqual({
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

  it('loads deployed bytecode from solc-style artifacts', () => {
    expect(
      loadContractArtifactFromJson({
        abi,
        contractName: 'Verifier',
        evm: {
          bytecode: { object: '6004' },
          deployedBytecode: { object: '0X6005' },
        },
      }),
    ).toEqual({
      abi,
      bytecode: '0x6004',
      deployedBytecode: '0x6005',
      contractName: 'Verifier',
    });
  });

  it('selects named artifacts from compiled contract maps without filesystem access', () => {
    const compiled = {
      contracts: {
        'contracts/Registry.sol': {
          Registry: { abi, bytecode: { object: '6006' } },
          Verifier: { abi, deployedBytecode: { object: '6007' } },
        },
      },
    };

    expect(loadContractArtifactFromJson(compiled, { contractName: 'Verifier' })).toEqual({
      abi,
      deployedBytecode: '0x6007',
      contractName: 'Verifier',
    });
    expect(load_contract_abi_from_json(compiled, { contractName: 'Registry' })).toEqual(abi);
  });

  it('returns Python-style dictionary fields through snake-case aliases', () => {
    expect(
      load_contract_artifact_from_json({ abi, bytecode: '6003', contractName: 'Registry' }),
    ).toEqual({
      abi,
      bytecode: '0x6003',
      contract_name: 'Registry',
    });
    expect(
      load_contract_artifact_from_json({
        abi,
        deployed_bytecode: '6008',
        contractName: 'Verifier',
      }),
    ).toEqual({
      abi,
      deployed_bytecode: '0x6008',
      contract_name: 'Verifier',
    });
  });

  it('omits empty bytecode and contract names', () => {
    expect(loadContractArtifactFromJson({ abi, bytecode: '0x', contractName: '   ' })).toEqual({
      abi,
    });
  });

  it('validates artifact and ABI shape', () => {
    expect(() => loadContractArtifactFromJson('[]')).toThrow('must be an object');
    expect(() => loadContractArtifactFromJson({ bytecode: '6000' })).toThrow("missing 'abi' list");
    expect(() => loadContractArtifactFromJson({ abi: ['not-object'] })).toThrow('ABI entries');
    expect(() => loadContractArtifactFromJson('{')).toThrow('could not be parsed');
    expect(() =>
      loadContractArtifactFromJson({
        contracts: {
          'Verifier.sol': {
            Registry: { abi },
            Verifier: { abi },
          },
        },
      }),
    ).toThrow('multiple compiled contracts');
    expect(() =>
      loadContractArtifactFromJson(
        { contracts: { 'Verifier.sol': { Verifier: { abi } } } },
        { contractName: 'Missing' },
      ),
    ).toThrow("Contract artifact 'Missing' was not found");
  });

  it('fails closed for filesystem path helpers in the browser port', () => {
    expect(() => loadContractArtifact('./Verifier.json')).toThrow(
      'Filesystem artifact path loading is not browser-native',
    );
    expect(() => loadContractAbi('./Verifier.json')).toThrow(
      'Filesystem artifact path loading is not browser-native',
    );
  });
});
