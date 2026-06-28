import {
  PortugueseParser,
  getPortugueseParserCapabilities,
  parsePortugueseDcec,
  parse_portuguese,
} from './portugueseParser';

describe('CEC Portuguese parser parity helpers', () => {
  it('ports portuguese_parser.py deontic legal patterns without runtime bridges', () => {
    const obligation = parsePortugueseDcec('O inquilino deve pagar a renda.');
    const permission = parse_portuguese('O senhorio pode entrar.');
    const prohibition = new PortugueseParser().parse_portuguese('O inquilino nao deve fumar.');

    expect(getPortugueseParserCapabilities()).toMatchObject({
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
      pythonModule: 'logic/CEC/nl/portuguese_parser.py',
    });
    expect(obligation).toMatchObject({
      ok: true,
      success: true,
      parse_method: 'browser_native_portuguese_parser',
      browser_native: true,
      normalized_text: 'o inquilino deve pagar a renda',
    });
    expect(obligation.english_text).toBe('tenant must pay rent');
    expect(obligation.dcec).toBe('O(pay_rent(tenant:Agent))');
    expect(permission.dcec).toBe('P(enter(landlord:Agent))');
    expect(prohibition.dcec).toBe('F(smoke(tenant:Agent))');
  });

  it('parses Portuguese temporal and connective forms into existing DCEC formulas', () => {
    const parser = new PortugueseParser();

    const result = parsePortugueseDcec('   ');

    expect(parser.parse('Sempre o inquilino deve pagar a renda.').dcec).toBe(
      '□(O(pay_rent(tenant:Agent)))',
    );
    expect(
      parser.parse('Se o inquilino deve pagar a renda entao o senhorio pode entrar.').dcec,
    ).toBe('(O(pay_rent(tenant:Agent)) → P(enter(landlord:Agent)))');
    expect(parser.parse('O inquilino deve pagar a renda e o senhorio pode inspecionar.').dcec).toBe(
      '(O(pay_rent(tenant:Agent)) ∧ P(inspect(landlord:Agent)))',
    );
    expect(result).toMatchObject({
      ok: false,
      success: false,
      fail_closed_reason: 'empty_input',
      browser_native: true,
    });
    expect(result.dcec_formula).toBeUndefined();
  });
});
