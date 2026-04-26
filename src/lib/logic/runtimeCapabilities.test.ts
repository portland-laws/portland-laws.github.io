import { getLogicRuntimeCapabilities } from './runtimeCapabilities';
import { convertLegalTextToDeontic } from './deontic';
import { parseFolText } from './fol';

describe('logic runtime capabilities', () => {
  it('declares browser-native mode with no server calls', () => {
    expect(getLogicRuntimeCapabilities()).toMatchObject({
      mode: 'browser_native',
      target: 'full_python_logic_parity_typescript_wasm',
      serverCallsAllowed: false,
      fol: {
        regexParser: true,
        nlpStatus: 'incomplete',
        nlpUnavailable: true,
        mlStatus: 'incomplete',
        mlUnavailable: true,
      },
      deontic: {
        ruleExtractor: true,
        mlStatus: 'incomplete',
        mlUnavailable: true,
      },
      proving: {
        lightweightReasoning: true,
        wasmProverStatus: 'incomplete',
        externalProverUnavailable: true,
      },
    });
  });

  it('surfaces temporary incomplete-port ML/NLP capabilities in converter outputs', () => {
    expect(parseFolText('All humans are mortal').capabilities).toEqual({
      nlpUnavailable: true,
      mlUnavailable: true,
      serverCallsAllowed: false,
    });

    expect(convertLegalTextToDeontic('The tenant must pay rent.').capabilities).toEqual({
      mlUnavailable: true,
      serverCallsAllowed: false,
    });
  });
});
