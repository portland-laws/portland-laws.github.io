import { canonicalizeJson, createBrowserLocalCid } from '../tdfol/ipfsCacheDemo';
import { ZKPProver, ZKPVerifier } from './facade';
import { ZKPProof, type ZKPProofDict } from './simulatedBackend';

export type ZkpIpfsPackage = {
  cid: string;
  theorem: string;
  axioms: Array<string>;
  proof: ZKPProofDict;
  verified: boolean;
  privateAxioms: boolean;
  canonicalJson: string;
  createdAt: number;
  metadata: Record<string, unknown>;
  sourcePythonModule: 'logic/zkp/examples/zkp_ipfs_integration.py';
};

export type BrowserNativeZkpIpfsTransport = {
  readonly mode: 'browser-native-ipfs';
  putPackage(item: ZkpIpfsPackage): Promise<string>;
  getPackage(cid: string): Promise<ZkpIpfsPackage | undefined>;
};

export type ZkpIpfsResult = {
  ok: boolean;
  cid: string;
  source: 'browser-memory' | 'browser-native-ipfs' | 'unavailable-ipfs-adapter';
  package?: ZkpIpfsPackage;
  verified?: boolean;
  error?: string;
};

export const ZKP_IPFS_INTEGRATION_METADATA = {
  sourcePythonModule: 'logic/zkp/examples/zkp_ipfs_integration.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  parity: [
    'deterministic_proof_package_cids',
    'local_simulated_zkp_generation',
    'injected_browser_ipfs_transport',
    'fail_closed_unavailable_adapter',
    'cid_verification_on_remote_reads',
    'private_axiom_redaction',
  ] as Array<string>,
} as const;

export class BrowserNativeZkpIpfsIntegration {
  private readonly packages = new Map<string, ZkpIpfsPackage>();
  private readonly now: () => number;
  private readonly prover: ZKPProver;
  private readonly verifier: ZKPVerifier;

  constructor(
    private readonly options: {
      now?: () => number;
      transport?: BrowserNativeZkpIpfsTransport;
      securityLevel?: number;
    } = {},
  ) {
    this.now = options.now ?? (() => Date.now());
    this.prover = new ZKPProver({ backend: 'simulated', securityLevel: options.securityLevel });
    this.verifier = new ZKPVerifier({ backend: 'simulated', securityLevel: options.securityLevel });
  }

  async proveAndStore(
    theorem: string,
    axioms: Array<string>,
    options: {
      metadata?: Record<string, unknown>;
      privateAxioms?: boolean;
    } = {},
  ): Promise<ZkpIpfsResult> {
    const normalizedAxioms = [...axioms].sort();
    const proof = await this.prover.generateProof(theorem, normalizedAxioms, {
      ...(options.metadata ?? {}),
      source_python_module: ZKP_IPFS_INTEGRATION_METADATA.sourcePythonModule,
    });
    const item = this.toPackage(
      theorem,
      normalizedAxioms,
      proof,
      await this.verifier.verifyProof(proof),
      options,
    );
    this.packages.set(item.cid, item);
    if (!this.options.transport)
      return { ok: true, cid: item.cid, source: 'browser-memory', package: item };
    const remoteCid = await this.options.transport.putPackage(item);
    return remoteCid === item.cid
      ? { ok: true, cid: item.cid, source: 'browser-native-ipfs', package: item }
      : {
          ok: false,
          cid: item.cid,
          source: 'browser-native-ipfs',
          package: item,
          error: `Injected IPFS transport returned ${remoteCid}`,
        };
  }

  async loadAndVerify(cid: string): Promise<ZkpIpfsResult> {
    const item = this.packages.get(cid) ?? (await this.options.transport?.getPackage(cid));
    if (!item)
      return {
        ok: false,
        cid,
        source: this.options.transport ? 'browser-native-ipfs' : 'unavailable-ipfs-adapter',
        error: this.options.transport
          ? 'ZKP proof package was not found.'
          : 'No browser-native IPFS transport was injected for ZKP proof packages.',
      };
    const source = this.packages.has(cid) ? 'browser-memory' : 'browser-native-ipfs';
    if (!verifyZkpIpfsPackage(item, cid))
      return {
        ok: false,
        cid,
        source,
        package: item,
        error: 'ZKP proof package CID verification failed.',
      };
    const verified = await this.verifier.verifyProof(ZKPProof.fromDict(item.proof));
    if (verified) this.packages.set(cid, item);
    return { ok: verified, cid, source, package: item, verified };
  }

  private toPackage(
    theorem: string,
    axioms: Array<string>,
    proof: ZKPProof,
    verified: boolean,
    options: {
      metadata?: Record<string, unknown>;
      privateAxioms?: boolean;
    },
  ): ZkpIpfsPackage {
    const body = {
      axioms: (options.privateAxioms ?? true) ? ['<private>'] : axioms,
      metadata: options.metadata ?? {},
      privateAxioms: options.privateAxioms ?? true,
      proof: { ...proof.toDict(), timestamp: 0 },
      sourcePythonModule: ZKP_IPFS_INTEGRATION_METADATA.sourcePythonModule,
      theorem,
      verified,
    };
    const canonicalJson = canonicalizeJson(body);
    return {
      ...body,
      canonicalJson,
      cid: createBrowserLocalCid(canonicalJson),
      createdAt: this.now(),
    };
  }
}

export function verifyZkpIpfsPackage(item: ZkpIpfsPackage, expectedCid: string): boolean {
  const canonicalJson = canonicalizeJson({
    axioms: item.axioms,
    metadata: item.metadata,
    privateAxioms: item.privateAxioms,
    proof: item.proof,
    sourcePythonModule: ZKP_IPFS_INTEGRATION_METADATA.sourcePythonModule,
    theorem: item.theorem,
    verified: item.verified,
  });
  return (
    item.cid === expectedCid &&
    item.sourcePythonModule === ZKP_IPFS_INTEGRATION_METADATA.sourcePythonModule &&
    item.canonicalJson === canonicalJson &&
    createBrowserLocalCid(canonicalJson) === expectedCid
  );
}

export const create_zkp_ipfs_integration = (
  options: ConstructorParameters<typeof BrowserNativeZkpIpfsIntegration>[0] = {},
): BrowserNativeZkpIpfsIntegration => new BrowserNativeZkpIpfsIntegration(options);
