import { createLogicApi, type LogicApiOptions } from './api';
import { validateBrowserNativeLogicRuntime } from './browserNativeValidation';
import type { BridgeProofRequest, LogicBridgeFormat } from './integration/bridge';

export type LogicCliCommand =
  | 'health'
  | 'convert'
  | 'prove'
  | 'policy'
  | 'evaluate-policy'
  | 'validate';
export interface LogicCliCommandSpec {
  readonly command: LogicCliCommand;
  readonly summary: string;
  readonly requiredFlags: readonly string[];
  readonly optionalFlags: readonly string[];
}
export interface LogicCliResult {
  ok: boolean;
  exitCode: 0 | 1 | 2;
  command?: LogicCliCommand;
  stdout: string;
  stderr: string;
  data?: Record<string, unknown>;
  runtime: Runtime;
}
export type LogicDevtoolsFlagValue = string | number | boolean | readonly string[];
export interface LogicDevtoolsCommandInvocation {
  command?: LogicCliCommand;
  argv?: readonly string[];
  flags?: Record<string, LogicDevtoolsFlagValue | undefined>;
}
export interface LogicDevtoolsCommandAdapter {
  readonly browserNative: true;
  readonly pythonRuntime: false;
  readonly serverRuntime: false;
  readonly commands: readonly LogicCliCommand[];
  readonly commandSpecs: readonly LogicCliCommandSpec[];
  run(invocation: LogicDevtoolsCommandInvocation): LogicCliResult;
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
const commandSpecs: readonly LogicCliCommandSpec[] = [
  spec('health', 'Report the browser-native logic runtime and supported commands.', [], ['json']),
  spec(
    'convert',
    'Convert logic text between supported local bridge formats.',
    ['source'],
    ['from', 'source-format', 'to', 'target-format', 'json'],
  ),
  spec(
    'prove',
    'Run a bounded browser-native proof request.',
    ['theorem', 'axiom'],
    ['logic', 'json'],
  ),
  spec(
    'policy',
    'Compile natural-language policy text into a local DCEC policy formula.',
    ['source'],
    ['json'],
  ),
  spec(
    'evaluate-policy',
    'Compile and evaluate a natural-language policy against a tool/action name.',
    ['source', 'tool'],
    ['actor', 'json'],
  ),
  spec(
    'validate',
    'Validate browser-native logic modules without server or Python fallbacks.',
    [],
    ['fol-text', 'deontic-text', 'json'],
  ),
];
const commands: readonly LogicCliCommand[] = commandSpecs.map((spec) => spec.command);
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
    return pass('health', `logic commands: ${commands.join(', ')}`, {
      commands: [...commands],
      command_specs: commandSpecs.map(commandSpecToData),
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
  const json = hasFlag(flags, 'json');
  const api = createLogicApi(options);
  if (command === 'health') {
    const data: Record<string, unknown> = {
      runtime: 'browser-native-typescript-wasm',
      commands: [...commands],
      command_specs: commandSpecs.map(commandSpecToData),
      ...runtime,
    };
    return pass(command, stdout('logic runtime: browser-native-typescript-wasm', data, json), data);
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
      : pass(
          command,
          stdout(String(data.target_formula ?? data.targetFormula ?? ''), data, json),
          data,
        );
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
      : pass(command, stdout(result.status, data, json), data);
  }
  if (command === 'policy') {
    const text = first(flags, 'source', 'text', 'input');
    if (text === undefined) {
      return fail(command, 2, 'policy requires --source <natural-language policy>.');
    }
    const result = api.compileNlToPolicy(text);
    const data: Record<string, unknown> = { ...result, command, ...runtime };
    return result.success
      ? pass(command, stdout(result.policyFormula, data, json), data)
      : fail(command, 1, result.warnings.join('; ') || 'policy compilation failed', data);
  }
  if (command === 'evaluate-policy') {
    const text = first(flags, 'source', 'text', 'input');
    const tool = first(flags, 'tool', 'action');
    if (text === undefined || tool === undefined) {
      return fail(command, 2, 'evaluate-policy requires --source <policy> and --tool <name>.');
    }
    const result = api.evaluateNlPolicy(text, { tool, actor: first(flags, 'actor') });
    const data: Record<string, unknown> = { ...result, command, ...runtime };
    return result.success
      ? pass(command, stdout(result.allowed ? 'allowed' : 'denied', data, json), data)
      : fail(command, 1, result.warnings.join('; ') || 'policy evaluation failed', data);
  }
  if (command === 'validate') {
    const data: Record<string, unknown> = {
      ...validateBrowserNativeLogicRuntime({
        folText: first(flags, 'fol-text', 'fol_text'),
        deonticText: first(flags, 'deontic-text', 'deontic_text'),
      }),
      command,
      ...runtime,
    };
    return data.valid === true
      ? pass(command, stdout('browser-native logic runtime valid', data, json), data)
      : fail(command, 1, 'browser-native logic runtime validation failed', data);
  }
  return fail(undefined, 2, `Unknown logic CLI command: ${String(command)}`);
}

export const run_logic_cli = runLogicCli;

export function describeLogicCliCommands(): readonly LogicCliCommandSpec[] {
  return commandSpecs;
}

export const describe_logic_cli_commands = describeLogicCliCommands;

export function createLogicDevtoolsCommandAdapter(
  options: LogicApiOptions = {},
): LogicDevtoolsCommandAdapter {
  return {
    browserNative: true,
    pythonRuntime: false,
    serverRuntime: false,
    commands,
    commandSpecs,
    run(invocation: LogicDevtoolsCommandInvocation): LogicCliResult {
      return runLogicCli(toArgv(invocation), options);
    },
  };
}

export function runLogicDevtoolsCommand(
  invocation: LogicDevtoolsCommandInvocation,
  options: LogicApiOptions = {},
): LogicCliResult {
  return createLogicDevtoolsCommandAdapter(options).run(invocation);
}

export const create_logic_devtools_command_adapter = createLogicDevtoolsCommandAdapter;
export const run_logic_devtools_command = runLogicDevtoolsCommand;

function toArgv(invocation: LogicDevtoolsCommandInvocation): readonly string[] {
  if (invocation.argv !== undefined) {
    return [...invocation.argv];
  }
  const argv: Array<string> = [];
  if (invocation.command !== undefined) {
    argv.push(invocation.command);
  }
  const flags = invocation.flags ?? {};
  for (const [key, value] of Object.entries(flags)) {
    if (value === undefined || value === false) {
      continue;
    }
    const flagValues = Array.isArray(value) ? value : [String(value)];
    for (const item of flagValues) {
      argv.push(`--${key}`);
      if (item !== 'true') {
        argv.push(item);
      }
    }
  }
  return argv;
}

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

function hasFlag(flags: Map<string, Array<string>>, key: string): boolean {
  return flags.has(key);
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

function spec(
  command: LogicCliCommand,
  summary: string,
  requiredFlags: readonly string[],
  optionalFlags: readonly string[],
): LogicCliCommandSpec {
  return { command, summary, requiredFlags, optionalFlags };
}

function commandSpecToData(spec: LogicCliCommandSpec): Record<string, unknown> {
  return {
    command: spec.command,
    summary: spec.summary,
    required_flags: [...spec.requiredFlags],
    optional_flags: [...spec.optionalFlags],
  };
}

function stdout(text: string, data: Record<string, unknown>, json: boolean): string {
  return json ? JSON.stringify(data) : text;
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
