import { CacheConfig, LogicConfig, MonitoringConfig, ProverConfig, SecurityConfig, getDefaultLogicConfig } from './config';

describe('logic config browser-native parity helpers', () => {
  it('models Python config dataclasses with snake_case dictionary serialization', () => {
    const config = new LogicConfig({
      provers: {
        native: new ProverConfig({ timeout: 2.5 }),
        z3: { enabled: false, timeout: 7, maxMemoryMb: 4096, options: { mode: 'wasm' } },
      },
      cache: new CacheConfig({ backend: 'memory', maxsize: 42, ttl: 30 }),
      security: new SecurityConfig({ rateLimitCalls: 10, enableAuditLog: false }),
      monitoring: new MonitoringConfig({ enabled: false, logLevel: 'DEBUG' }),
    });

    expect(config.toDict()).toMatchObject({
      provers: {
        native: { enabled: true, timeout: 2.5, max_memory_mb: 2048 },
        z3: { enabled: false, timeout: 7, max_memory_mb: 4096, options: { mode: 'wasm' } },
      },
      cache: { backend: 'memory', maxsize: 42, ttl: 30 },
      security: { rate_limit_calls: 10, enable_audit_log: false },
      monitoring: { enabled: false, log_level: 'DEBUG' },
    });
  });

  it('loads Python-style object data without filesystem or YAML dependencies', () => {
    const config = LogicConfig.fromObject({
      provers: {
        cvc5: { enabled: true, timeout: 11, max_memory_mb: 512 },
      },
      cache: { backend: 'memory', maxsize: 5, redis_url: 'redis://ignored-in-browser' },
      security: { max_text_length: 250, enable_input_validation: false },
      monitoring: { enable_tracing: true, tracing_backend: 'opentelemetry' },
    });

    expect(config.provers.cvc5).toMatchObject({
      enabled: true,
      timeout: 11,
      maxMemoryMb: 512,
    });
    expect(config.cache.redisUrl).toBe('redis://ignored-in-browser');
    expect(config.security.enableInputValidation).toBe(false);
    expect(config.monitoring.enableTracing).toBe(true);
  });

  it('loads from an explicit env record instead of process.env', () => {
    const config = LogicConfig.fromEnv({
      Z3_ENABLED: 'false',
      Z3_TIMEOUT: '9.5',
      Z3_MAX_MEMORY_MB: '1024',
      SYMBOLICAI_API_KEY: 'fixture-only',
      SYMBOLICAI_MODEL: 'local-browser-model',
      SYMBOLICAI_TEMPERATURE: '0.2',
      CACHE_MAXSIZE: '123',
      RATE_LIMIT_CALLS: '12',
      ENABLE_MONITORING: 'false',
      LOG_LEVEL: 'WARN',
      ENABLE_TRACING: 'true',
    });

    expect(config.provers.z3).toMatchObject({
      enabled: false,
      timeout: 9.5,
      maxMemoryMb: 1024,
    });
    expect(config.provers.symbolicai.options).toMatchObject({
      model: 'local-browser-model',
      temperature: 0.2,
    });
    expect(config.cache.maxsize).toBe(123);
    expect(config.security.rateLimitCalls).toBe(12);
    expect(config.monitoring).toMatchObject({ enabled: false, logLevel: 'WARN', enableTracing: true });
  });

  it('keeps default prover inventory aligned with the Python module', () => {
    const config = getDefaultLogicConfig();

    expect(Object.keys(config.provers).sort()).toEqual(['coq', 'cvc5', 'lean', 'native', 'symbolicai', 'z3']);
    expect(config.provers.native.enabled).toBe(true);
    expect(config.provers.lean.enabled).toBe(false);
    expect(config.cache.backend).toBe('memory');
    expect(config.monitoring.metricsBackend).toBe('prometheus');
  });
});
