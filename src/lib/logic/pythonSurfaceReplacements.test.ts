import { createPythonSurfaceReplacementPlan } from './pythonSurfaceReplacements';

describe('createPythonSurfaceReplacementPlan', () => {
  it('maps known Python API and CLI surfaces to browser-native replacements', () => {
    const plan = createPythonSurfaceReplacementPlan([
      'ipfs_datasets_py.logic_api',
      'ipfs_datasets_py.cli',
      'python -m ipfs_datasets_py',
    ]);

    expect(plan.browserNative).toBe(true);
    expect(plan.usesPythonRuntime).toBe(false);
    expect(plan.usesServerRuntime).toBe(false);
    expect(plan.rejectedSurfaces).toEqual([]);
    expect(plan.replacements.map((replacement) => replacement.replacementKind)).toEqual([
      'typescript-developer-script',
      'browser-devtools',
      'browser-devtools',
    ]);
    expect(
      plan.replacements.every(
        (replacement) =>
          replacement.browserNative &&
          !replacement.usesPythonRuntime &&
          !replacement.usesServerRuntime,
      ),
    ).toBe(true);
  });

  it('infers TypeScript developer script replacements for Python API module surfaces', () => {
    const plan = createPythonSurfaceReplacementPlan([
      ' ipfs_datasets_py.formal_logic.converter ',
      'ipfs_datasets_py.formal_logic.converter',
    ]);

    expect(plan.rejectedSurfaces).toEqual([]);
    expect(plan.replacements).toHaveLength(1);
    expect(plan.replacements[0]).toMatchObject({
      pythonSurface: 'ipfs_datasets_py.formal_logic.converter',
      surfaceKind: 'api',
      replacementKind: 'typescript-developer-script',
      replacementName: 'logic TypeScript module imports',
      browserNative: true,
      usesPythonRuntime: false,
      usesServerRuntime: false,
    });
  });

  it('fails closed for server, filesystem, subprocess, and raw Python fallbacks', () => {
    const plan = createPythonSurfaceReplacementPlan([
      'http://localhost:8000/convert',
      'file:///tmp/input.json',
      'subprocess:ipfs_datasets_py.cli',
      'scripts/export_logic.py',
      'python scripts/export_logic.py',
    ]);

    expect(plan.replacements).toEqual([]);
    expect(plan.rejectedSurfaces).toEqual([
      'http://localhost:8000/convert',
      'file:///tmp/input.json',
      'subprocess:ipfs_datasets_py.cli',
      'scripts/export_logic.py',
      'python scripts/export_logic.py',
    ]);
  });
});
