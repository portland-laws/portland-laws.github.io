import {
  FOL_CONSTRUCTOR_IO_METADATA,
  INTERACTIVE_FOL_CONSTRUCTOR_METADATA,
  createBrowserNativeFolConstructorIo,
  createBrowserNativeInteractiveFolConstructor,
  create_browser_native_interactive_fol_constructor,
  create_browser_native_fol_constructor_io,
} from './folConstructorIo';
import {
  INTERACTIVE_FOL_TYPES_METADATA,
  checkInteractiveFolType,
  interactive_fol_type_descriptors,
  is_interactive_fol_type,
} from './interactiveFolTypes';

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

describe('Interactive FOL types', () => {
  it('ports interactive_fol_types.py descriptors and fail-closed shape guards', () => {
    const prompt = { id: 'prompt-1', role: 'user', content: 'All tenants are residents.' };
    const turn = { prompt, formula: '(∀x (Tenants(x) → Residents(x)))', valid: true, warnings: [] };
    expect(INTERACTIVE_FOL_TYPES_METADATA).toEqual({
      sourcePythonModule: 'logic/integration/interactive/interactive_fol_types.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntime: false,
      runtimeDependencies: [],
    });
    expect(interactive_fol_type_descriptors.session.requiredFields).toEqual([
      'id',
      'prompts',
      'turns',
    ]);
    expect(checkInteractiveFolType('prompt', prompt)).toMatchObject({ ok: true, issues: [] });
    expect(checkInteractiveFolType('turn', turn)).toMatchObject({ ok: true, issues: [] });
    expect(is_interactive_fol_type('symbol', { name: 'Tenant', kind: 'predicate' })).toBe(true);
    expect(
      checkInteractiveFolType('prompt', { id: 'bad', role: 'tool', content: 12 }),
    ).toMatchObject({
      ok: false,
      issues: [
        { path: '$.role', message: 'expected_prompt_role' },
        { path: '$.content', message: 'expected_string' },
      ],
    });
  });
});

describe('BrowserNativeInteractiveFolConstructor', () => {
  it('ports interactive_fol_constructor.py as a browser-native construction facade', () => {
    const constructor = createBrowserNativeInteractiveFolConstructor();
    const result = constructor.construct('All permits are approvals. No approval is expired.', {
      sessionId: 'interactive-case-1',
    });

    expect(constructor.metadata).toBe(INTERACTIVE_FOL_CONSTRUCTOR_METADATA);
    expect(result).toMatchObject({
      ok: true,
      formula: '(∀x (Permits(x) → Approvals(x))) ∧ (∀x (Approval(x) → ¬Expired(x)))',
      questions: [],
    });
    expect(result.symbols).toContainEqual({ name: 'x', kind: 'variable' });
  });

  it('continues sessions and asks deterministic clarification questions fail-closed', () => {
    const constructor = create_browser_native_interactive_fol_constructor();
    const first = constructor.construct('Tenant provides notice');
    const next = constructor.continueSession(first.session, 'If tenant then resident');

    expect(first).toMatchObject({
      ok: true,
      formula: '(Notice(x))',
      questions: [
        { id: 'question-missing-quantifier', reason: 'missing_quantifier' },
        { id: 'question-missing-relation', reason: 'missing_relation' },
      ],
    });
    expect(next.session.prompts).toHaveLength(2);
    expect(next).toMatchObject({
      ok: true,
      formula: '(∀x (Tenant(x) → Resident(x)))',
      questions: [],
    });
    expect(constructor.construct('   ')).toMatchObject({
      ok: false,
      questions: [{ id: 'question-empty-input', reason: 'empty_input' }],
      errors: ['empty_prompt'],
    });
  });
});
