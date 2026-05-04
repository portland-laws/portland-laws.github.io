import {
  BrowserNativeModalLogicExtension,
  MODAL_LOGIC_EXTENSION_METADATA,
  convert_modal_logic_extension,
} from './modalLogicExtension';

describe('BrowserNativeModalLogicExtension', () => {
  it('ports modal_logic_extension.py as local modal projection with tableaux validation', () => {
    const extension = new BrowserNativeModalLogicExtension({
      outputFormat: 'json',
      runTableaux: true,
    });
    const result = extension.convert(
      'The tenant must pay rent. The landlord may enter after notice. The agency shall not disclose sealed records.',
    );

    expect(extension.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/converters/modal_logic_extension.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(result).toMatchObject({
      status: 'success',
      success: true,
      outputFormat: 'json',
      formulas: [
        'box(Tenant_PayRent)',
        'diamond(Landlord_EnterAfterNotice)',
        'box(not(Agency_DiscloseSealedRecords))',
      ],
      metadata: { clause_count: 3, tableaux_checked: true, serverCallsAllowed: false },
      tableaux: { metadata: { browserNative: true, pythonFallback: false } },
    });
    expect(result.clauses.map((clause) => clause.operator)).toEqual([
      'necessary',
      'possible',
      'necessary',
    ]);
  });

  it('supports Python aliases, output formats, batch conversion, and fail-closed validation', () => {
    expect(MODAL_LOGIC_EXTENSION_METADATA.parity).toContain('modal_operator_extraction');
    const extension = new BrowserNativeModalLogicExtension();

    expect(
      extension.convert('Users may appeal decisions.', { outputFormat: 'prolog' }).output,
    ).toBe('modal_clause(1, "diamond(Users_AppealDecisions)").');
    expect(extension.convert('Users must file notices.', { outputFormat: 'tptp' }).output).toBe(
      'fof(modal_clause_1, axiom, "box(Users_FileNotices)").',
    );
    expect(
      extension.convertBatch(['Auditors must inspect logs.', 'Operators can pause jobs.']),
    ).toEqual([
      expect.objectContaining({ success: true, formulas: ['box(Auditors_InspectLogs)'] }),
      expect.objectContaining({ success: true, formulas: ['diamond(Operators_PauseJobs)'] }),
    ]);
    expect(convert_modal_logic_extension('x')).toMatchObject({
      status: 'validation_failed',
      success: false,
      metadata: {
        sourcePythonModule: 'logic/integration/converters/modal_logic_extension.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
    });
  });
});
