export interface ProverConfigInit {
  enabled?: boolean;
  timeout?: number;
  maxMemoryMb?: number;
  options?: Record<string, unknown>;
}

export interface CacheConfigInit {
  backend?: 'memory' | 'redis' | string;
  maxsize?: number;
  ttl?: number;
  redisUrl?: string;
  redisDb?: number;
  enablePersistence?: boolean;
  persistencePath?: string;
}

export interface SecurityConfigInit {
  rateLimitCalls?: number;
  rateLimitPeriod?: number;
  maxTextLength?: number;
  maxFormulaDepth?: number;
  maxFormulaComplexity?: number;
  enableAuditLog?: boolean;
  auditLogPath?: string;
  enableInputValidation?: boolean;
}

export interface MonitoringConfigInit {
  enabled?: boolean;
  port?: number;
  logLevel?: string;
  metricsBackend?: 'prometheus' | 'statsd' | string;
  enableTracing?: boolean;
  tracingBackend?: string;
}

export interface LogicConfigInit {
  provers?: Record<string, ProverConfig | ProverConfigInit>;
  cache?: CacheConfig | CacheConfigInit;
  security?: SecurityConfig | SecurityConfigInit;
  monitoring?: MonitoringConfig | MonitoringConfigInit;
}

export type LogicEnvironment = Record<string, string | undefined>;

export class ProverConfig {
  readonly enabled: boolean;
  readonly timeout: number;
  readonly maxMemoryMb: number;
  readonly options: Record<string, unknown>;

  constructor(init: ProverConfigInit = {}) {
    this.enabled = init.enabled ?? true;
    this.timeout = init.timeout ?? 5.0;
    this.maxMemoryMb = init.maxMemoryMb ?? 2048;
    this.options = { ...(init.options ?? {}) };
  }

  toDict(): Record<string, unknown> {
    return {
      enabled: this.enabled,
      timeout: this.timeout,
      max_memory_mb: this.maxMemoryMb,
      options: { ...this.options },
    };
  }
}

export class CacheConfig {
  readonly backend: string;
  readonly maxsize: number;
  readonly ttl: number;
  readonly redisUrl?: string;
  readonly redisDb: number;
  readonly enablePersistence: boolean;
  readonly persistencePath?: string;

  constructor(init: CacheConfigInit = {}) {
    this.backend = init.backend ?? 'memory';
    this.maxsize = init.maxsize ?? 10000;
    this.ttl = init.ttl ?? 3600;
    this.redisUrl = init.redisUrl;
    this.redisDb = init.redisDb ?? 0;
    this.enablePersistence = init.enablePersistence ?? false;
    this.persistencePath = init.persistencePath;
  }

  toDict(): Record<string, unknown> {
    return {
      backend: this.backend,
      maxsize: this.maxsize,
      ttl: this.ttl,
      redis_url: this.redisUrl,
      redis_db: this.redisDb,
      enable_persistence: this.enablePersistence,
      persistence_path: this.persistencePath,
    };
  }
}

export class SecurityConfig {
  readonly rateLimitCalls: number;
  readonly rateLimitPeriod: number;
  readonly maxTextLength: number;
  readonly maxFormulaDepth: number;
  readonly maxFormulaComplexity: number;
  readonly enableAuditLog: boolean;
  readonly auditLogPath?: string;
  readonly enableInputValidation: boolean;

  constructor(init: SecurityConfigInit = {}) {
    this.rateLimitCalls = init.rateLimitCalls ?? 100;
    this.rateLimitPeriod = init.rateLimitPeriod ?? 60;
    this.maxTextLength = init.maxTextLength ?? 10000;
    this.maxFormulaDepth = init.maxFormulaDepth ?? 100;
    this.maxFormulaComplexity = init.maxFormulaComplexity ?? 1000;
    this.enableAuditLog = init.enableAuditLog ?? true;
    this.auditLogPath = init.auditLogPath;
    this.enableInputValidation = init.enableInputValidation ?? true;
  }

  toDict(): Record<string, unknown> {
    return {
      rate_limit_calls: this.rateLimitCalls,
      rate_limit_period: this.rateLimitPeriod,
      max_text_length: this.maxTextLength,
      max_formula_depth: this.maxFormulaDepth,
      max_formula_complexity: this.maxFormulaComplexity,
      enable_audit_log: this.enableAuditLog,
      audit_log_path: this.auditLogPath,
      enable_input_validation: this.enableInputValidation,
    };
  }
}

export class MonitoringConfig {
  readonly enabled: boolean;
  readonly port: number;
  readonly logLevel: string;
  readonly metricsBackend: string;
  readonly enableTracing: boolean;
  readonly tracingBackend: string;

  constructor(init: MonitoringConfigInit = {}) {
    this.enabled = init.enabled ?? true;
    this.port = init.port ?? 9090;
    this.logLevel = init.logLevel ?? 'INFO';
    this.metricsBackend = init.metricsBackend ?? 'prometheus';
    this.enableTracing = init.enableTracing ?? false;
    this.tracingBackend = init.tracingBackend ?? 'opentelemetry';
  }

  toDict(): Record<string, unknown> {
    return {
      enabled: this.enabled,
      port: this.port,
      log_level: this.logLevel,
      metrics_backend: this.metricsBackend,
      enable_tracing: this.enableTracing,
      tracing_backend: this.tracingBackend,
    };
  }
}

export class LogicConfig {
  readonly provers: Record<string, ProverConfig>;
  readonly cache: CacheConfig;
  readonly security: SecurityConfig;
  readonly monitoring: MonitoringConfig;

  constructor(init: LogicConfigInit = {}) {
    this.provers = Object.fromEntries(
      Object.entries(init.provers ?? defaultProvers()).map(([name, config]) => [
        name,
        config instanceof ProverConfig ? config : new ProverConfig(config),
      ]),
    );
    this.cache = init.cache instanceof CacheConfig ? init.cache : new CacheConfig(init.cache);
    this.security = init.security instanceof SecurityConfig ? init.security : new SecurityConfig(init.security);
    this.monitoring = init.monitoring instanceof MonitoringConfig ? init.monitoring : new MonitoringConfig(init.monitoring);
  }

  static fromObject(data: Record<string, unknown>): LogicConfig {
    return new LogicConfig({
      provers: parseProvers(data.provers),
      cache: parseCacheConfig(data.cache),
      security: parseSecurityConfig(data.security),
      monitoring: parseMonitoringConfig(data.monitoring),
    });
  }

  static fromEnv(env: LogicEnvironment): LogicConfig {
    return new LogicConfig({
      provers: {
        native: new ProverConfig({
          enabled: true,
          timeout: envFloat(env, 'NATIVE_TIMEOUT', 5.0),
        }),
        z3: new ProverConfig({
          enabled: envBool(env, 'Z3_ENABLED', true),
          timeout: envFloat(env, 'Z3_TIMEOUT', 5.0),
          maxMemoryMb: envInt(env, 'Z3_MAX_MEMORY_MB', 2048),
        }),
        cvc5: new ProverConfig({
          enabled: envBool(env, 'CVC5_ENABLED', false),
          timeout: envFloat(env, 'CVC5_TIMEOUT', 10.0),
        }),
        symbolicai: new ProverConfig({
          enabled: Boolean(env.SYMBOLICAI_API_KEY),
          timeout: envFloat(env, 'SYMBOLICAI_TIMEOUT', 10.0),
          options: {
            model: env.SYMBOLICAI_MODEL ?? 'gpt-4',
            temperature: envFloat(env, 'SYMBOLICAI_TEMPERATURE', 0.0),
          },
        }),
      },
      cache: new CacheConfig({
        backend: env.CACHE_BACKEND ?? 'memory',
        maxsize: envInt(env, 'CACHE_MAXSIZE', 10000),
        ttl: envInt(env, 'CACHE_TTL', 3600),
        redisUrl: env.REDIS_URL,
        redisDb: envInt(env, 'REDIS_DB', 0),
      }),
      security: new SecurityConfig({
        rateLimitCalls: envInt(env, 'RATE_LIMIT_CALLS', 100),
        rateLimitPeriod: envInt(env, 'RATE_LIMIT_PERIOD', 60),
        maxTextLength: envInt(env, 'MAX_TEXT_LENGTH', 10000),
        maxFormulaDepth: envInt(env, 'MAX_FORMULA_DEPTH', 100),
        maxFormulaComplexity: envInt(env, 'MAX_FORMULA_COMPLEXITY', 1000),
        enableAuditLog: envBool(env, 'ENABLE_AUDIT_LOG', true),
        auditLogPath: env.AUDIT_LOG_PATH,
      }),
      monitoring: new MonitoringConfig({
        enabled: envBool(env, 'ENABLE_MONITORING', true),
        port: envInt(env, 'METRICS_PORT', 9090),
        logLevel: env.LOG_LEVEL ?? 'INFO',
        enableTracing: envBool(env, 'ENABLE_TRACING', false),
      }),
    });
  }

  toDict(): Record<string, unknown> {
    return {
      provers: Object.fromEntries(Object.entries(this.provers).map(([name, config]) => [name, config.toDict()])),
      cache: this.cache.toDict(),
      security: this.security.toDict(),
      monitoring: this.monitoring.toDict(),
    };
  }
}

export function getDefaultLogicConfig(): LogicConfig {
  return new LogicConfig();
}

export const get_config = getDefaultLogicConfig;

function defaultProvers(): Record<string, ProverConfig> {
  return {
    native: new ProverConfig({ enabled: true, timeout: 5.0 }),
    z3: new ProverConfig({ enabled: true, timeout: 5.0 }),
    cvc5: new ProverConfig({ enabled: false, timeout: 10.0 }),
    lean: new ProverConfig({ enabled: false, timeout: 30.0 }),
    coq: new ProverConfig({ enabled: false, timeout: 30.0 }),
    symbolicai: new ProverConfig({ enabled: false, timeout: 10.0 }),
  };
}

function parseProvers(value: unknown): Record<string, ProverConfig> | undefined {
  if (!isPlainObject(value)) return undefined;
  return Object.fromEntries(
    Object.entries(value).map(([name, rawConfig]) => [name, new ProverConfig(parseProverConfig(rawConfig))]),
  );
}

function parseProverConfig(value: unknown): ProverConfigInit {
  if (!isPlainObject(value)) return {};
  return {
    enabled: asBoolean(value.enabled),
    timeout: asNumber(value.timeout),
    maxMemoryMb: asNumber(value.max_memory_mb ?? value.maxMemoryMb),
    options: isPlainObject(value.options) ? value.options : undefined,
  };
}

function parseCacheConfig(value: unknown): CacheConfigInit | undefined {
  if (!isPlainObject(value)) return undefined;
  return {
    backend: asString(value.backend),
    maxsize: asNumber(value.maxsize),
    ttl: asNumber(value.ttl),
    redisUrl: asString(value.redis_url ?? value.redisUrl),
    redisDb: asNumber(value.redis_db ?? value.redisDb),
    enablePersistence: asBoolean(value.enable_persistence ?? value.enablePersistence),
    persistencePath: asString(value.persistence_path ?? value.persistencePath),
  };
}

function parseSecurityConfig(value: unknown): SecurityConfigInit | undefined {
  if (!isPlainObject(value)) return undefined;
  return {
    rateLimitCalls: asNumber(value.rate_limit_calls ?? value.rateLimitCalls),
    rateLimitPeriod: asNumber(value.rate_limit_period ?? value.rateLimitPeriod),
    maxTextLength: asNumber(value.max_text_length ?? value.maxTextLength),
    maxFormulaDepth: asNumber(value.max_formula_depth ?? value.maxFormulaDepth),
    maxFormulaComplexity: asNumber(value.max_formula_complexity ?? value.maxFormulaComplexity),
    enableAuditLog: asBoolean(value.enable_audit_log ?? value.enableAuditLog),
    auditLogPath: asString(value.audit_log_path ?? value.auditLogPath),
    enableInputValidation: asBoolean(value.enable_input_validation ?? value.enableInputValidation),
  };
}

function parseMonitoringConfig(value: unknown): MonitoringConfigInit | undefined {
  if (!isPlainObject(value)) return undefined;
  return {
    enabled: asBoolean(value.enabled),
    port: asNumber(value.port),
    logLevel: asString(value.log_level ?? value.logLevel),
    metricsBackend: asString(value.metrics_backend ?? value.metricsBackend),
    enableTracing: asBoolean(value.enable_tracing ?? value.enableTracing),
    tracingBackend: asString(value.tracing_backend ?? value.tracingBackend),
  };
}

function envBool(env: LogicEnvironment, key: string, fallback: boolean): boolean {
  const value = env[key];
  if (value === undefined) return fallback;
  return value.toLowerCase() === 'true';
}

function envInt(env: LogicEnvironment, key: string, fallback: number): number {
  const parsed = Number.parseInt(env[key] ?? '', 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function envFloat(env: LogicEnvironment, key: string, fallback: number): number {
  const parsed = Number.parseFloat(env[key] ?? '');
  return Number.isFinite(parsed) ? parsed : fallback;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function asBoolean(value: unknown): boolean | undefined {
  return typeof value === 'boolean' ? value : undefined;
}

function asNumber(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
}

function asString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined;
}
