import {
  FOL_CONSTRUCTOR_IO_METADATA,
  createBrowserNativeFolConstructorIo,
  create_browser_native_fol_constructor_io,
} from './folConstructorIo';

describe('BrowserNativeFolConstructorIo', () => {
  it('ports _fol_constructor_io.py prompt/session I/O without runtime fallbacks', () => {
    const io = createBrowserNativeFolConstructorIo();
    const result = io.appendPrompt(
      io.createSession('case-1'),
      'All tenants are residents. No tenant is exempt.',
    );

    expect(io.metadata).toEqual({
      sourcePythonModule: 'logic/integration/interactive/_fol_constructor_io.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntime: false,
      runtimeDependencies: [],
    });
    expect(result).toMatchObject({
      ok: true,
      formula: '(∀x (Tenants(x) → Residents(x))) ∧ (∀x (Tenant(x) → ¬Exempt(x)))',
      metadata: FOL_CONSTRUCTOR_IO_METADATA,
    });
    expect(result.session.prompts[0]).toMatchObject({
      id: 'prompt-all-tenants-are-residents-no-tenant-is-exempt',
      role: 'user',
    });
    expect(result.session.turns[0]).toMatchObject({ valid: true, warnings: [] });
  });

  it('serializes, parses, and fails closed on invalid constructor I/O', () => {
    const io = create_browser_native_fol_constructor_io();
    const result = io.appendPrompt(io.createSession('case-2'), {
      id: 'explicit',
      role: 'assistant',
      content: 'If tenant then resident',
    });
    const restored = io.parseSession(io.serializeSession(result.session));

    expect(restored).toMatchObject({ ok: true, formula: '(∀x (Tenant(x) → Resident(x)))' });
    expect(restored.session.prompts[0]).toMatchObject({ id: 'explicit', role: 'assistant' });
    expect(io.parseSession('{')).toMatchObject({
      ok: false,
      errors: ['invalid_json'],
      metadata: {
        sourcePythonModule: 'logic/integration/interactive/_fol_constructor_io.py',
        serverCallsAllowed: false,
        pythonRuntime: false,
      },
    });
    expect(io.appendPrompt(restored.session, '   ')).toMatchObject({
      ok: false,
      errors: ['empty_prompt'],
    });
  });
});
