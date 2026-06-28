import type { BrowserNativeProofLogic } from './proverAdapters';

export type BrowserNativeInstallableProver =
  | 'e-prover'
  | 'cvc5'
  | 'z3'
  | 'lean'
  | 'symbolicai'
  | 'coq'
  | 'vampire';

export interface BrowserNativeProverInstallMetadata {
  sourcePythonModule: 'logic/integration/bridges/prover_installer.py';
  runtime: 'typescript-wasm-browser';
  serverCallsAllowed: false;
  pythonRuntime: false;
  subprocessAllowed: false;
  filesystemAllowed: false;
  packageManagerAllowed: false;
  failClosed: true;
}

export interface BrowserNativeProverInstallTarget {
  name: BrowserNativeInstallableProver;
  available: boolean;
  installableInBrowser: false;
  supportedLogics: Array<BrowserNativeProofLogic>;
  localAdapter: string | null;
  browserNativeReplacement: string | null;
  blockedOperations: Array<'filesystem' | 'subprocess' | 'package-manager' | 'python-runtime'>;
  reason: string;
}
export interface BrowserNativeProverInstallPlan {
  metadata: BrowserNativeProverInstallMetadata;
  target: BrowserNativeProverInstallTarget;
  status: 'already-local' | 'blocked';
  actions: string[];
  warnings: string[];
}
const METADATA: BrowserNativeProverInstallMetadata = {
  sourcePythonModule: 'logic/integration/bridges/prover_installer.py',
  runtime: 'typescript-wasm-browser',
  serverCallsAllowed: false,
  pythonRuntime: false,
  subprocessAllowed: false,
  filesystemAllowed: false,
  packageManagerAllowed: false,
  failClosed: true,
};
const BLOCKED_OPERATIONS: BrowserNativeProverInstallTarget['blockedOperations'] = [
  'filesystem',
  'subprocess',
  'package-manager',
  'python-runtime',
];
const TARGETS: Array<BrowserNativeProverInstallTarget> = [
  target(
    'e-prover',
    ['tdfol'],
    'browser-native-e-prover-adapter',
    'local TDFOL prover with TPTP metadata',
  ),
  target(
    'cvc5',
    ['tdfol'],
    'browser-native-cvc5-prover-bridge',
    'local TDFOL prover with SMT-LIB metadata',
  ),
  target(
    'z3',
    ['tdfol'],
    'browser-native-z3-prover-bridge',
    'local TDFOL prover with SMT-LIB metadata',
  ),
  target(
    'lean',
    ['tdfol'],
    'browser-native-lean-prover-bridge',
    'local TDFOL prover with Lean metadata',
  ),
  target(
    'symbolicai',
    ['tdfol'],
    'browser-native-symbolicai-prover-bridge',
    'deterministic symbolic adapter',
  ),
  target('coq', [], null, null),
  target('vampire', [], null, null),
];
export class BrowserNativeProverInstaller {
  readonly metadata = METADATA;

  listTargets(): Array<BrowserNativeProverInstallTarget> {
    return TARGETS.map((candidate) => ({ ...candidate }));
  }

  getTarget(name: BrowserNativeInstallableProver): BrowserNativeProverInstallTarget {
    const found = TARGETS.find((candidate) => candidate.name === name);
    if (found) return { ...found };
    return target(name, [], null, null);
  }
  planInstall(name: BrowserNativeInstallableProver): BrowserNativeProverInstallPlan {
    const selected = this.getTarget(name);
    const alreadyLocal = selected.available && selected.localAdapter !== null;
    return {
      metadata: { ...this.metadata },
      target: selected,
      status: alreadyLocal ? 'already-local' : 'blocked',
      actions: alreadyLocal
        ? [`Use ${selected.localAdapter} from the browser-native integration bridge.`]
        : [],
      warnings: [alreadyLocal ? localWarning(name) : blockedWarning(name)],
    };
  }
  install(name: BrowserNativeInstallableProver): BrowserNativeProverInstallPlan {
    const plan = this.planInstall(name);
    if (plan.status === 'already-local') return plan;
    throw new Error(plan.warnings[0]);
  }
}
export function createBrowserNativeProverInstaller(): BrowserNativeProverInstaller {
  return new BrowserNativeProverInstaller();
}
export const create_browser_native_prover_installer = createBrowserNativeProverInstaller;
function target(
  name: BrowserNativeInstallableProver,
  supportedLogics: Array<BrowserNativeProofLogic>,
  localAdapter: string | null,
  browserNativeReplacement: string | null,
): BrowserNativeProverInstallTarget {
  return {
    name,
    available: localAdapter !== null,
    installableInBrowser: false,
    supportedLogics,
    localAdapter,
    browserNativeReplacement,
    blockedOperations: BLOCKED_OPERATIONS,
    reason:
      localAdapter === null
        ? 'No bundled browser-native TypeScript/WASM adapter exists for this prover.'
        : 'A bundled browser-native adapter replaces installer-side binary discovery.',
  };
}
function localWarning(name: BrowserNativeInstallableProver): string {
  return `${name} binary installation is not attempted; the browser-native adapter is already bundled.`;
}
function blockedWarning(name: BrowserNativeInstallableProver): string {
  return `${name} cannot be installed from browser code because filesystem, subprocess, package-manager, and Python runtime access are disabled.`;
}
