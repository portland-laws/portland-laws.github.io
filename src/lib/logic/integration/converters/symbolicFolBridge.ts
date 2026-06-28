import { SymbolicFOLBridge, type SymbolicFOLBridgeOptions } from '../symbolicFolBridge';

export class SymbolicFOLConverterBridge extends SymbolicFOLBridge {
  constructor(options: Omit<SymbolicFOLBridgeOptions, 'sourcePythonModule'> = {}) {
    super({
      ...options,
      sourcePythonModule: 'logic/integration/converters/symbolic_fol_bridge.py',
    });
  }
}

export const BrowserNativeSymbolicFOLConverterBridge = SymbolicFOLConverterBridge;

export function createBrowserNativeSymbolicFOLConverterBridge(
  options: Omit<SymbolicFOLBridgeOptions, 'sourcePythonModule'> = {},
): SymbolicFOLConverterBridge {
  return new SymbolicFOLConverterBridge(options);
}
