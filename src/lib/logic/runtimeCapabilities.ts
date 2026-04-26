export type LogicRuntimeMode = 'browser_native';
export type LogicPortTarget = 'full_python_logic_parity_typescript_wasm';
export type LogicCapabilityStatus = 'complete' | 'incomplete';

export interface LogicRuntimeCapabilities {
  mode: LogicRuntimeMode;
  target: LogicPortTarget;
  serverCallsAllowed: false;
  fol: {
    regexParser: true;
    nlpStatus: LogicCapabilityStatus;
    browserNativeNlp: boolean;
    nlpUnavailable: boolean;
    mlStatus: LogicCapabilityStatus;
    browserNativeMlConfidence: boolean;
    mlUnavailable: boolean;
  };
  deontic: {
    ruleExtractor: true;
    mlStatus: LogicCapabilityStatus;
    browserNativeMlConfidence: boolean;
    mlUnavailable: boolean;
  };
  proving: {
    lightweightReasoning: true;
    wasmProverStatus: LogicCapabilityStatus;
    externalProverUnavailable: true;
    browserWasmProver: boolean;
  };
}

export function getLogicRuntimeCapabilities(): LogicRuntimeCapabilities {
  return {
    mode: 'browser_native',
    target: 'full_python_logic_parity_typescript_wasm',
    serverCallsAllowed: false,
    fol: {
      regexParser: true,
      nlpStatus: 'incomplete',
      browserNativeNlp: false,
      nlpUnavailable: true,
      mlStatus: 'incomplete',
      browserNativeMlConfidence: false,
      mlUnavailable: true,
    },
    deontic: {
      ruleExtractor: true,
      mlStatus: 'incomplete',
      browserNativeMlConfidence: false,
      mlUnavailable: true,
    },
    proving: {
      lightweightReasoning: true,
      wasmProverStatus: 'incomplete',
      externalProverUnavailable: true,
      browserWasmProver: false,
    },
  };
}
