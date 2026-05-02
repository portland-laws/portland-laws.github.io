export type DomainIntegrationRuntime = 'browser-native' | 'wasm-compatible' | 'fail-closed';

export type ForbiddenIntegrationRuntime =
  | 'python-service'
  | 'node-filesystem'
  | 'rust-ffi'
  | 'subprocess'
  | 'rpc-server'
  | 'server-fallback';

export type BridgeCapability =
  | 'domain-policy-normalization'
  | 'interactive-workflow-validation'
  | 'parity-fixture-metadata'
  | 'fail-closed-adapter';

export interface BridgeMetadataMap {
  readonly [key: string]: string | number | boolean | readonly string[] | undefined;
}

export interface ParityFixtureMetadata {
  readonly fixtureId: string;
  readonly sourceLogic: 'ipfs_datasets_py.logic';
  readonly capturedWith: 'python-parity-fixture' | 'typescript-contract';
  readonly deterministic: boolean;
  readonly coverage: readonly string[];
}

export interface InteractiveWorkflowSpec {
  readonly id: string;
  readonly label: string;
  readonly requiredFacts: readonly string[];
  readonly allowedActions: readonly string[];
  readonly guardrails: readonly string[];
}

export interface DomainBridgeInput {
  readonly bridgeId: string;
  readonly domain: string;
  readonly runtime: DomainIntegrationRuntime | ForbiddenIntegrationRuntime | string;
  readonly capabilities?: readonly BridgeCapability[];
  readonly workflows?: readonly InteractiveWorkflowSpec[];
  readonly fixture?: ParityFixtureMetadata;
  readonly metadata?: BridgeMetadataMap;
}

export interface DomainIntegrationBridge {
  readonly bridgeId: string;
  readonly domain: string;
  readonly runtime: DomainIntegrationRuntime;
  readonly accepted: boolean;
  readonly capabilities: readonly BridgeCapability[];
  readonly workflows: readonly InteractiveWorkflowSpec[];
  readonly fixture?: ParityFixtureMetadata;
  readonly metadata: BridgeMetadataMap;
  readonly validationIssues: readonly string[];
  readonly browserNative: true;
  readonly wasmCompatible: boolean;
  readonly serverCallsAllowed: false;
  readonly pythonServiceAllowed: false;
}

export interface WorkflowActionRequest {
  readonly workflowId: string;
  readonly actionId: string;
  readonly suppliedFacts?: readonly string[];
  readonly acknowledgedGuardrails?: readonly string[];
}

export interface WorkflowActionValidation {
  readonly accepted: boolean;
  readonly reason:
    | 'accepted'
    | 'unknown_workflow'
    | 'unknown_action'
    | 'missing_facts'
    | 'unacknowledged_guardrails';
  readonly missingFacts: readonly string[];
  readonly unacknowledgedGuardrails: readonly string[];
}

const ALLOWED_RUNTIMES: readonly DomainIntegrationRuntime[] = [
  'browser-native',
  'wasm-compatible',
  'fail-closed',
];

const FORBIDDEN_RUNTIMES: readonly string[] = [
  'python-service',
  'node-filesystem',
  'rust-ffi',
  'subprocess',
  'rpc-server',
  'server-fallback',
];

export function createDomainIntegrationBridge(input: DomainBridgeInput): DomainIntegrationBridge {
  const validationIssues = validateDomainBridgeInput(input);
  const accepted = validationIssues.length === 0 && input.runtime !== 'fail-closed';
  const runtime = accepted && isAllowedRuntime(input.runtime) ? input.runtime : 'fail-closed';
  const capabilities = normalizeCapabilities(input.capabilities, accepted);

  return {
    bridgeId: input.bridgeId,
    domain: input.domain,
    runtime,
    accepted,
    capabilities,
    workflows: [...(input.workflows ?? [])],
    fixture: input.fixture,
    metadata: {
      ...(input.metadata ?? {}),
      adapter_contract: accepted ? 'browser_native_domain_bridge' : 'fail_closed_domain_bridge',
    },
    validationIssues,
    browserNative: true,
    wasmCompatible: runtime === 'browser-native' || runtime === 'wasm-compatible',
    serverCallsAllowed: false,
    pythonServiceAllowed: false,
  };
}

export function validateWorkflowAction(
  bridge: DomainIntegrationBridge,
  request: WorkflowActionRequest,
): WorkflowActionValidation {
  const workflow = bridge.workflows.find((candidate) => candidate.id === request.workflowId);
  if (!workflow) {
    return rejectWorkflowAction('unknown_workflow');
  }
  if (!workflow.allowedActions.includes(request.actionId)) {
    return rejectWorkflowAction('unknown_action');
  }

  const suppliedFacts = new Set(request.suppliedFacts ?? []);
  const missingFacts = workflow.requiredFacts.filter((fact) => !suppliedFacts.has(fact));
  if (missingFacts.length > 0) {
    return {
      accepted: false,
      reason: 'missing_facts',
      missingFacts,
      unacknowledgedGuardrails: [],
    };
  }

  const acknowledgedGuardrails = new Set(request.acknowledgedGuardrails ?? []);
  const unacknowledgedGuardrails = workflow.guardrails.filter(
    (guardrail) => !acknowledgedGuardrails.has(guardrail),
  );
  if (unacknowledgedGuardrails.length > 0) {
    return {
      accepted: false,
      reason: 'unacknowledged_guardrails',
      missingFacts: [],
      unacknowledgedGuardrails,
    };
  }

  return {
    accepted: bridge.accepted,
    reason: bridge.accepted ? 'accepted' : 'unacknowledged_guardrails',
    missingFacts: [],
    unacknowledgedGuardrails: bridge.accepted ? [] : workflow.guardrails,
  };
}

export function createParityFixtureMetadata(
  fixtureId: string,
  coverage: readonly string[],
): ParityFixtureMetadata {
  return {
    fixtureId,
    sourceLogic: 'ipfs_datasets_py.logic',
    capturedWith: 'typescript-contract',
    deterministic: true,
    coverage: [...coverage],
  };
}

function validateDomainBridgeInput(input: DomainBridgeInput): string[] {
  const issues: string[] = [];
  if (input.bridgeId.trim().length === 0) issues.push('bridgeId is required');
  if (input.domain.trim().length === 0) issues.push('domain is required');
  if (FORBIDDEN_RUNTIMES.includes(input.runtime))
    issues.push(`forbidden runtime: ${input.runtime}`);
  if (!isAllowedRuntime(input.runtime)) issues.push(`unsupported runtime: ${input.runtime}`);
  if (input.fixture && input.fixture.deterministic !== true) {
    issues.push('parity fixture metadata must be deterministic');
  }
  return issues;
}

function isAllowedRuntime(runtime: string): runtime is DomainIntegrationRuntime {
  return ALLOWED_RUNTIMES.includes(runtime as DomainIntegrationRuntime);
}

function normalizeCapabilities(
  capabilities: readonly BridgeCapability[] | undefined,
  accepted: boolean,
): readonly BridgeCapability[] {
  const normalized = new Set(capabilities ?? []);
  normalized.add('domain-policy-normalization');
  normalized.add('interactive-workflow-validation');
  normalized.add('parity-fixture-metadata');
  if (!accepted) normalized.add('fail-closed-adapter');
  return [...normalized];
}

function rejectWorkflowAction(
  reason: WorkflowActionValidation['reason'],
): WorkflowActionValidation {
  return {
    accepted: false,
    reason,
    missingFacts: [],
    unacknowledgedGuardrails: [],
  };
}
