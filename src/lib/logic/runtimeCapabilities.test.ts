import { getLogicRuntimeCapabilities } from './runtimeCapabilities';
import { convertLegalTextToDeontic } from './deontic';
import { parseFolText } from './fol';

describe('logic runtime capabilities', () => {
  it('declares browser-native mode with no server calls', () => {
    expect(getLogicRuntimeCapabilities()).toMatchObject({
      mode: 'browser_native',
      serverCallsAllowed: false,
      fol: {
        regexParser: true,
        nlpUnavailable: true,
        mlUnavailable: true,
      },
      deontic: {
        ruleExtractor: true,
        mlUnavailable: true,
      },
      proving: {
        lightweightReasoning: true,
        externalProverUnavailable: true,
      },
    });
  });

  it('surfaces unavailable ML/NLP capabilities in converter outputs', () => {
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
