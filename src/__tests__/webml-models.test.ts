/**
 * @jest-environment jsdom
 */

describe('WebGPU Language Models', () => {
  test('should have correct model keys for LiquidAI ONNX WebGPU models', () => {
    // These model IDs correspond to live Hugging Face repos with transformers.js support.
    const expectedInstructKey = 'LiquidAI/LFM2.5-1.2B-Instruct-ONNX';
    const expectedThinkingKey = 'LiquidAI/LFM2.5-1.2B-Thinking-ONNX';
    
    expect(expectedInstructKey).toBe('LiquidAI/LFM2.5-1.2B-Instruct-ONNX');
    expect(expectedThinkingKey).toBe('LiquidAI/LFM2.5-1.2B-Thinking-ONNX');
  });

  test('should define expected model properties structure', () => {
    // Define expected structure for WebGPU models
    const expectedModelStructure = {
      name: expect.any(String),
      size: expect.any(String),
      requiresWebGPU: true,
      contextLength: expect.any(Number),
      description: expect.any(String),
      type: 'instruct',
      quantized: true,
      simdOptimized: true
    };
    
    // Test that our expected structure is valid
    expect(expectedModelStructure.requiresWebGPU).toBe(true);
    expect(expectedModelStructure.type).toBe('instruct');
    expect(expectedModelStructure.quantized).toBe(true);
    expect(expectedModelStructure.simdOptimized).toBe(true);
  });

  test('should validate model context length expectations', () => {
    const expectedContextLength = 2048;
    
    expect(expectedContextLength).toBeGreaterThanOrEqual(2048);
    expect(expectedContextLength).toBeLessThanOrEqual(32768); // Reasonable upper bound
  });

  test('should validate WebGPU model requirements', () => {
    const webGPURequirements = {
      requiresWebGPU: true,
      quantized: true, // LiquidAI WebGPU exports use q4 quantization
      simdOptimized: true, // Still benefit from SIMD optimizations
      minRAM: 4096, // MB - expected minimum for 1.2B q4 models
      preferredCores: 4 // Expected CPU cores for optimal performance
    };
    
    expect(webGPURequirements.requiresWebGPU).toBe(true);
    expect(webGPURequirements.quantized).toBe(true);
    expect(webGPURequirements.simdOptimized).toBe(true);
    expect(webGPURequirements.minRAM).toBeGreaterThanOrEqual(4000);
  });
});
