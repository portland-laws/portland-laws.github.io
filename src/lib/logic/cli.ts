import { createLogicApi, type LogicApiOptions } from './api';
import type { BridgeProofRequest, LogicBridgeFormat } from './integration/bridge';

export type LogicCliCommand = 'health' | 'convert' | 'prove' | 'policy';
export interface LogicCliResult {
  ok: boolean;
  exitCode: 0 | 1 | 2;
  command?: LogicCliCommand;
  stdout: string;
  stderr: string;
  data?: Record<string, unknown>;
  runtime: Runtime;
}
type Runtime = {
  browserNative: true;
  pythonRuntime: false;
  serverRuntime: false;
  serverCallsAllowed: false;
};

const runtime: Runtime = {
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
  serverCallsAllowed: false,
};
const formats: readonly LogicBridgeFormat[] = [
  'natural_language',
  'legal_text',
  'fol',
  'deontic',
  'tdfol',
  'cec',
  'dcec',
  'prolog',
  'tptp',
  'json',
  'defeasible',
];
const blockedRuntime =
  /(?:^|\s)(?:python|python3|py|pip|uv|node|curl)\b|https?:\/\/|file:\/\/|subprocess|rpc:\/\//i;

export function runLogicCli(
  argv: readonly string[],
  options: LogicApiOptions = {},
): LogicCliResult {
  const args = [...argv];
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    return pass('health', 'logic commands: health, convert, prove, policy', {
      commands: ['health', 'convert', 'prove', 'policy'],
    });
  }
  if (blockedRuntime.test(args.join(' '))) {
    return fail(
      undefined,
      2,
      'Runtime fallbacks are not available for browser-native logic CLI commands.',
    );
  }

  const command = args.shift() as LogicCliCommand;
  const flags = parseFlags(args);
  const api = createLogicApi(options);
  if (command === 'health') {
    return pass(command, 'logic runtime: browser-native-typescript-wasm', {
      runtime: 'browser-native-typescript-wasm',
      ...runtime,
    });
  }
  if (command === 'convert') {
    const source = first(flags, 'source', 'text', 'input');
    if (source === undefined) {
      return fail(command, 2, 'convert requires --source <text>.');
    }
    const result = api.convertLogic(
      source,
      format(flags, 'from', 'source-format', 'source_format') ?? 'natural_language',
      format(flags, 'to', 'target-format', 'target_format') ?? 'fol',
    );
    const data: Record<string, unknown> = { ...result.toDict(), command, ...runtime };
    return result.status === 'failed' || result.status === 'unsupported'
      ? fail(command, 1, String(data.error ?? data.status), data)
      : pass(command, String(data.target_formula ?? data.targetFormula ?? ''), data);
  }
  if (command === 'prove') {
    const theorem = first(flags, 'theorem', 'goal');
    const axioms = values(flags, 'axiom', 'axioms');
    if (theorem === undefined || axioms.length === 0) {
      return fail(
        command,
        2,
        'prove requires --theorem <formula> and at least one --axiom <formula>.',
      );
    }
    const result = api.prove({ logic: proofLogic(flags) ?? 'cec', theorem, axioms });
    const data: Record<string, unknown> = { ...result, command, ...runtime };
    return result.status === 'error'
      ? fail(command, 1, result.error ?? 'proof failed', data)
      : pass(command, result.status, data);
  }
  if (command === 'policy') {
    const text = first(flags, 'source', 'text', 'input');
    if (text === undefined) {
      return fail(command, 2, 'policy requires --source <natural-language policy>.');
    }
    const result = api.compileNlToPolicy(text);
    const data: Record<string, unknown> = { ...result, command, ...runtime };
    return result.success
      ? pass(command, result.policyFormula, data)
      : fail(command, 1, result.warnings.join('; ') || 'policy compilation failed', data);
  }
  return fail(undefined, 2, `Unknown logic CLI command: ${String(command)}`);
}

export const run_logic_cli = runLogicCli;

function parseFlags(args: readonly string[]): Map<string, Array<string>> {
  const flags = new Map<string, Array<string>>();
  for (let index = 0; index < args.length; index += 1) {
    const raw = args[index];
    if (!raw.startsWith('--')) {
      continue;
    }
    const next = args[index + 1];
    const value = next !== undefined && !next.startsWith('--') ? next : 'true';
    if (value !== 'true') {
      index += 1;
    }
    flags.set(raw.slice(2), [...(flags.get(raw.slice(2)) ?? []), value]);
  }
  return flags;
}

function first(flags: Map<string, Array<string>>, ...keys: readonly string[]): string | undefined {
  for (const key of keys) {
    const value = flags.get(key)?.[0];
    if (value !== undefined && value.trim().length > 0) {
      return value;
    }
  }
  return undefined;
}

function values(flags: Map<string, Array<string>>, ...keys: readonly string[]): string[] {
  return keys.flatMap((key) => flags.get(key) ?? []).filter((value) => value.trim().length > 0);
}

function format(
  flags: Map<string, Array<string>>,
  ...keys: readonly string[]
): LogicBridgeFormat | undefined {
  const value = first(flags, ...keys);
  return value !== undefined && formats.includes(value as LogicBridgeFormat)
    ? (value as LogicBridgeFormat)
    : undefined;
}

function proofLogic(flags: Map<string, Array<string>>): BridgeProofRequest['logic'] | undefined {
  const value = first(flags, 'logic');
  return value === 'tdfol' || value === 'cec' || value === 'dcec' ? value : undefined;
}

function pass(
  command: LogicCliCommand,
  stdout: string,
  data: Record<string, unknown>,
): LogicCliResult {
  return { ok: true, exitCode: 0, command, stdout, stderr: '', data, runtime };
}

function fail(
  command: LogicCliCommand | undefined,
  exitCode: 1 | 2,
  stderr: string,
  data?: Record<string, unknown>,
): LogicCliResult {
  return { ok: false, exitCode, command, stdout: '', stderr, data, runtime };
}
