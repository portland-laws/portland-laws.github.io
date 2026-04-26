export type LogicRuntimeMode = 'browser_native';

export interface LogicRuntimeCapabilities {
  mode: LogicRuntimeMode;
  serverCallsAllowed: false;
  fol: {
    regexParser: true;
    browserNativeNlp: boolean;
    nlpUnavailable: boolean;
    browserNativeMlConfidence: boolean;
    mlUnavailable: boolean;
  };
  deontic: {
    ruleExtractor: true;
    browserNativeMlConfidence: boolean;
    mlUnavailable: boolean;
  };
  proving: {
    lightweightReasoning: true;
    externalProverUnavailable: true;
    browserWasmProver: boolean;
  };
}

export function getLogicRuntimeCapabilities(): LogicRuntimeCapabilities {
  return {
    mode: 'browser_native',
    serverCallsAllowed: false,
    fol: {
      regexParser: true,
      browserNativeNlp: false,
      nlpUnavailable: true,
      browserNativeMlConfidence: false,
      mlUnavailable: true,
    },
    deontic: {
      ruleExtractor: true,
      browserNativeMlConfidence: false,
      mlUnavailable: true,
    },
    proving: {
      lightweightReasoning: true,
      externalProverUnavailable: true,
      browserWasmProver: false,
    },
  };
}

