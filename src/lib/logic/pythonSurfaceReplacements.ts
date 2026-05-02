export type PythonSurfaceKind = 'api' | 'cli';

export type BrowserNativeReplacementKind = 'typescript-developer-script' | 'browser-devtools';

export interface PythonSurfaceReplacement {
  readonly pythonSurface: string;
  readonly surfaceKind: PythonSurfaceKind;
  readonly replacementKind: BrowserNativeReplacementKind;
  readonly replacementName: string;
  readonly browserNative: true;
  readonly usesPythonRuntime: false;
  readonly usesServerRuntime: false;
  readonly notes: readonly string[];
}

export interface PythonSurfaceReplacementPlan {
  readonly replacements: readonly PythonSurfaceReplacement[];
  readonly rejectedSurfaces: readonly string[];
  readonly browserNative: true;
  readonly usesPythonRuntime: false;
  readonly usesServerRuntime: false;
}

const PYTHON_RUNTIME_MARKERS = [
  'python ',
  'python3 ',
  'py ',
  'pip ',
  'uv run python',
  'subprocess',
  'rpc://',
  'http://localhost',
  'https://localhost',
  'file://',
  '.py',
];

const DEFAULT_REPLACEMENTS: readonly PythonSurfaceReplacement[] = [
  {
    pythonSurface: 'ipfs_datasets_py.logic_api',
    surfaceKind: 'api',
    replacementKind: 'typescript-developer-script',
    replacementName: 'logic TypeScript module imports',
    browserNative: true,
    usesPythonRuntime: false,
    usesServerRuntime: false,
    notes: [
      'Import deterministic logic modules directly from src/lib/logic.',
      'Keep validation data serializable so browser tests and devtools can inspect it without filesystem access.',
    ],
  },
  {
    pythonSurface: 'ipfs_datasets_py.cli',
    surfaceKind: 'cli',
    replacementKind: 'browser-devtools',
    replacementName: 'browser console diagnostics',
    browserNative: true,
    usesPythonRuntime: false,
    usesServerRuntime: false,
    notes: [
      'Expose deterministic conversion and validation helpers through browser-loaded TypeScript modules.',
      'Do not shell out, open local files, or proxy to a Python process from browser runtime code.',
    ],
  },
  {
    pythonSurface: 'python -m ipfs_datasets_py',
    surfaceKind: 'cli',
    replacementKind: 'browser-devtools',
    replacementName: 'browser console diagnostics',
    browserNative: true,
    usesPythonRuntime: false,
    usesServerRuntime: false,
    notes: [
      'Treat Python module execution as a legacy CLI surface only.',
      'Use browser-native TypeScript diagnostics instead of spawning Python.',
    ],
  },
];

function normalizeSurface(surface: string): string {
  return surface.trim().replace(/\s+/g, ' ');
}

function containsRuntimeFallback(surface: string): boolean {
  const normalized = normalizeSurface(surface).toLowerCase();
  return PYTHON_RUNTIME_MARKERS.some((marker) => normalized.includes(marker));
}

function inferReplacement(surface: string): PythonSurfaceReplacement | undefined {
  const normalized = normalizeSurface(surface);
  const exact = DEFAULT_REPLACEMENTS.find(
    (replacement) => replacement.pythonSurface === normalized,
  );

  if (exact) {
    return exact;
  }

  if (normalized.startsWith('ipfs_datasets_py.') && !containsRuntimeFallback(normalized)) {
    return {
      pythonSurface: normalized,
      surfaceKind: 'api',
      replacementKind: 'typescript-developer-script',
      replacementName: 'logic TypeScript module imports',
      browserNative: true,
      usesPythonRuntime: false,
      usesServerRuntime: false,
      notes: [
        'Port this Python API surface as deterministic TypeScript before exposing it to browser callers.',
        'Reject adapters that require Python, subprocesses, local files, RPC, or server endpoints.',
      ],
    };
  }

  return undefined;
}

export function createPythonSurfaceReplacementPlan(
  surfaces: readonly string[],
): PythonSurfaceReplacementPlan {
  const replacements: PythonSurfaceReplacement[] = [];
  const rejectedSurfaces: string[] = [];
  const seen = new Set();

  for (const surface of surfaces) {
    const normalized = normalizeSurface(surface);
    if (normalized.length === 0 || seen.has(normalized)) {
      continue;
    }

    seen.add(normalized);
    const replacement = inferReplacement(normalized);

    if (replacement && !containsRuntimeFallback(replacement.replacementName)) {
      replacements.push(replacement);
    } else {
      rejectedSurfaces.push(normalized);
    }
  }

  return {
    replacements,
    rejectedSurfaces,
    browserNative: true,
    usesPythonRuntime: false,
    usesServerRuntime: false,
  };
}
