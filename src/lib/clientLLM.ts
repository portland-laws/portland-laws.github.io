import type { TextGenerationPipeline } from '@huggingface/transformers';
import { LLM_CONFIG, SUPPORTED_MODELS } from './llmConfig';
import { backendDetector } from './backendDetection';
import { openRouterLLMService } from './openRouterLLM';

// Model configuration interface
export interface ModelConfig {
  name: string;
  size: string;
  requiresWebGPU: boolean;
  contextLength: number;
  description: string;
  type: 'instruct' | 'conversational';
  quantized: boolean;
  simdOptimized: boolean;
  preferredDtype?: 'fp32' | 'fp16' | 'q8' | 'q4';
  padTokenId?: number;
  stopTokens?: readonly string[];
}

// Enhanced client-side LLM service with WebGPU support for larger models
class ClientLLMService {
  private textGenerator: TextGenerationPipeline | null = null;
  private isLoading = false;
  private currentModel: string = LLM_CONFIG.CLIENT_MODEL;
  private supportedModels = SUPPORTED_MODELS;
  private transformersPromise: Promise<{ pipeline: any; env: any }> | null = null;

  constructor() {
    // Models are now loaded from centralized config
  }

  private async getTransformers() {
    if (!this.transformersPromise) {
      this.transformersPromise = (async () => {
        const transformers = await import('@huggingface/transformers');
        transformers.env.allowLocalModels = false;
        transformers.env.useBrowserCache = true;
        return { pipeline: transformers.pipeline, env: transformers.env };
      })();
    }
    return this.transformersPromise;
  }

  async initialize(modelName?: string): Promise<void> {
    const targetModel = modelName || this.currentModel;
    
    if (this.textGenerator && this.currentModel === targetModel) return;
    if (this.isLoading) return;
    
    this.isLoading = true;
    try {
      // Check backend capabilities for model compatibility
      const capabilities = await backendDetector.detectCapabilities();
      const modelConfig = this.supportedModels[targetModel as keyof typeof SUPPORTED_MODELS] as ModelConfig | undefined;
      
      // Enhanced WebGPU diagnostics for large model compatibility
      if (modelConfig?.requiresWebGPU) {
        const webgpuDiagnostics = await backendDetector.getWebGPUDiagnostics();
        
        if (!webgpuDiagnostics.available) {
          console.warn(`Model ${targetModel} requires WebGPU but it's not available. Falling back to DistilGPT-2.`);
          this.isLoading = false;
          return this.initialize('Xenova/distilgpt2');
        }
        
        // Check if WebGPU setup is suitable for large models
        if (!webgpuDiagnostics.suitableForLargeModels && modelConfig.size.includes('GB')) {
          console.warn(`WebGPU adapter may not be suitable for large model ${targetModel}. Consider using a smaller model.`);
          console.log('WebGPU diagnostics:', {
            vendor: webgpuDiagnostics.adapter?.vendor,
            description: webgpuDiagnostics.adapter?.description,
            suitableForLargeModels: webgpuDiagnostics.suitableForLargeModels
          });
        }
      }

      // Configure transformers.js for optimal performance
      if (capabilities.webgpu && modelConfig?.requiresWebGPU) {
        // Try to initialize WebGPU properly for transformers.js
        const webgpuInit = await backendDetector.initializeWebGPUForTransformers();
        console.log('WebGPU initialization:', webgpuInit.message);
        
        if (!webgpuInit.success) {
          console.warn(`WebGPU initialization failed: ${webgpuInit.message}. Falling back to DistilGPT-2.`);
          this.isLoading = false;
          return this.initialize('Xenova/distilgpt2');
        }

        // Set execution providers for ONNX Runtime with better error handling
        try {
          const { env } = await this.getTransformers();
          if (env.backends?.onnx) {
            // Set WebGPU as the preferred execution provider with CPU as final fallback
            (env.backends.onnx as any).executionProviders = ['webgpu', 'wasm', 'cpu'];
            console.log('Set execution providers: WebGPU (primary), WASM (fallback), CPU (final)');
            
            // Add execution provider error handling
            if (env.backends.onnx.webgpu) {
              try {
                (env.backends.onnx.webgpu as any).contextTimeoutMs = 10000; // 10 second timeout
              } catch {
                // Ignore if property doesn't exist
              }
            }
          }
        } catch (epError) {
          console.warn('Could not set execution providers:', epError);
          // Continue without WebGPU if configuration fails
        }
      } else {
        // Use WASM/CPU fallback
        try {
          const { env } = await this.getTransformers();
          if (env.backends?.onnx) {
            (env.backends.onnx as any).executionProviders = ['wasm', 'cpu'];
            if (env.backends.onnx.wasm) {
              (env.backends.onnx.wasm as any).useGpu = false;
            }
          }
        } catch {
          // Ignore if not available
        }
      }

      // Import env for thread configuration
      const { env, pipeline } = await this.getTransformers();
      
      // Set appropriate thread count based on device capabilities
      if (capabilities.threads && env.backends?.onnx?.wasm) {
        (env.backends.onnx.wasm as any).numThreads = Math.min(navigator.hardwareConcurrency, 4);
      }

      console.log(`Initializing ${modelConfig?.name || targetModel}...`);
      
      // Configure pipeline options based on available backends
      const pipelineOptions: any = {};

      // If WebGPU is available and model requires it, configure WebGPU device
      if (capabilities.webgpu && modelConfig?.requiresWebGPU) {
        pipelineOptions.device = 'webgpu'; // Use WebGPU device
        pipelineOptions.dtype = modelConfig?.preferredDtype || 'q4'; // Use quantized WebGPU weights to save browser memory
        console.log('Configuring pipeline for WebGPU with q4 precision');
      } else if (capabilities.wasm) {
        pipelineOptions.device = 'wasm'; // Explicitly use WASM
        pipelineOptions.dtype = modelConfig?.quantized ? 'q8' : undefined;
        console.log('Configuring pipeline for WASM backend');
      }

      const createPipeline = pipeline as any;
      try {
        this.textGenerator = await createPipeline('text-generation', targetModel, pipelineOptions) as TextGenerationPipeline;
        this.currentModel = targetModel;
        console.log(`Successfully loaded ${modelConfig?.name || targetModel}`);
      } catch (pipelineError) {
        console.warn('Pipeline creation failed, attempting fallback:', pipelineError);
        
        // If WebGPU pipeline fails, try WASM fallback
        if (pipelineOptions.device === 'webgpu') {
          console.log('WebGPU pipeline failed, falling back to WASM...');
          const fallbackOptions = {
            ...pipelineOptions,
            device: 'wasm',
            dtype: 'q8',
          };
          
          try {
            this.textGenerator = await createPipeline('text-generation', targetModel, fallbackOptions) as TextGenerationPipeline;
            this.currentModel = targetModel;
            console.log(`Successfully loaded ${modelConfig?.name || targetModel} with WASM fallback`);
          } catch (fallbackError) {
            console.error('WASM fallback also failed:', fallbackError);
            throw fallbackError;
          }
        } else {
          throw pipelineError;
        }
      }
    } catch (error) {
      console.error('Failed to initialize client-side LLM:', error);
      
      // Fallback to smaller model if large model fails
      if (targetModel !== 'Xenova/distilgpt2') {
        console.log('Falling back to DistilGPT-2...');
        this.isLoading = false;
        return this.initialize('Xenova/distilgpt2');
      }
      
      throw error;
    } finally {
      this.isLoading = false;
    }
  }

  async generateResponse(prompt: string, maxTokens: number = 100): Promise<string> {
    if (this.isLoading && openRouterLLMService.isConfigured()) {
      return openRouterLLMService.generateText(prompt, {
        maxTokens,
        model: this.getOpenRouterModelForCurrentModel(),
        temperature: this.currentModel.includes('Thinking') ? 0.1 : 0.1,
        topP: this.currentModel.includes('Thinking') ? 0.1 : undefined,
        topK: 50,
        repetitionPenalty: 1.05,
      });
    }

    if (!this.textGenerator) {
      try {
        await this.initialize();
      } catch (error) {
        if (openRouterLLMService.isConfigured()) {
          console.warn('Local LLM initialize failed; using OpenRouter fallback', error);
          return openRouterLLMService.generateText(prompt, {
            maxTokens,
            model: this.getOpenRouterModelForCurrentModel(),
            temperature: this.currentModel.includes('Thinking') ? 0.1 : 0.1,
            topP: this.currentModel.includes('Thinking') ? 0.1 : undefined,
            topK: 50,
            repetitionPenalty: 1.05,
          });
        }
        throw error;
      }
    }

    if (!this.textGenerator) {
      throw new Error('Failed to initialize text generator');
    }

    try {
      const modelConfig = this.supportedModels[this.currentModel as keyof typeof SUPPORTED_MODELS] as ModelConfig | undefined;
      const isInstructModel = this.currentModel.includes('Instruct') || 
                             this.currentModel.includes('Thinking') ||
                             modelConfig?.type === 'instruct';
      
      // Format prompt appropriately for instruction models
      let formattedPrompt: string | Array<{ role: string; content: string }> = prompt;
      
      if (isInstructModel) {
        formattedPrompt = [
          { role: 'system', content: 'You are a concise, helpful assistant.' },
          { role: 'user', content: prompt },
        ];
      }

      const generationOptions: any = {
        max_new_tokens: maxTokens,
        temperature: isInstructModel ? 0.1 : 0.7,
        do_sample: true,
        repetition_penalty: isInstructModel ? 1.05 : 1.1,
      };
      if (isInstructModel && this.currentModel.includes('Thinking')) {
        generationOptions.top_p = 0.1;
      } else {
        generationOptions.top_p = 0.9;
      }
      if (isInstructModel) {
        generationOptions.top_k = 50;
      }
      if (modelConfig?.padTokenId !== undefined) {
        generationOptions.pad_token_id = modelConfig.padTokenId;
      } else if (!isInstructModel) {
        generationOptions.pad_token_id = 50256;
      }

      const response = await this.textGenerator(formattedPrompt as any, generationOptions) as any;

      // Extract the generated text, removing the input prompt
      let generatedText = this.extractGeneratedText(response, formattedPrompt);
      
      // Clean up instruction model responses
      generatedText = this.stripStopTokens(generatedText, modelConfig?.stopTokens);
      
      return generatedText;
    } catch (error) {
      console.error('Error generating response:', error);
      if (openRouterLLMService.isConfigured()) {
        console.warn('Using OpenRouter fallback after local generation failure');
        return openRouterLLMService.generateText(prompt, {
          maxTokens,
          model: this.getOpenRouterModelForCurrentModel(),
          temperature: this.currentModel.includes('Thinking') ? 0.1 : 0.1,
          topP: this.currentModel.includes('Thinking') ? 0.1 : undefined,
          topK: 50,
          repetitionPenalty: 1.05,
        });
      }
      throw error;
    }
  }

  async generateConversationMessage(
    characterName: string,
    identity: string,
    conversationHistory: string[],
    type: 'start' | 'continue' | 'leave',
    otherCharacterName?: string
  ): Promise<string> {
    let prompt = `You are ${characterName}. ${identity}\n\n`;
    
    if (type === 'start') {
      prompt += `You are starting a conversation with ${otherCharacterName}. Say hello and introduce yourself naturally.\n\n`;
      prompt += `${characterName}:`;
    } else if (type === 'continue') {
      prompt += `Conversation history:\n`;
      conversationHistory.forEach(message => {
        prompt += `${message}\n`;
      });
      prompt += `\nContinue the conversation naturally as ${characterName}.\n\n`;
      prompt += `${characterName}:`;
    } else if (type === 'leave') {
      prompt += `Conversation history:\n`;
      conversationHistory.forEach(message => {
        prompt += `${message}\n`;
      });
      prompt += `\nYou want to politely end this conversation. Say goodbye naturally.\n\n`;
      prompt += `${characterName}:`;
    }

    const maxTokens = type === 'start' ? 50 : type === 'leave' ? 30 : 80;
    let response = await this.generateResponse(prompt, maxTokens);
    
    // Clean up the response
    response = this.cleanResponse(response, characterName, otherCharacterName);
    
    return response;
  }

  private extractGeneratedText(response: any, formattedPrompt: string | Array<{ role: string; content: string }>): string {
    const first = Array.isArray(response) ? response[0] : response;
    const generated = first?.generated_text;

    if (Array.isArray(generated)) {
      const lastMessage = generated[generated.length - 1];
      return String(lastMessage?.content || '').trim();
    }

    const fullText = String(generated || '');
    if (typeof formattedPrompt === 'string' && fullText.startsWith(formattedPrompt)) {
      return fullText.slice(formattedPrompt.length).trim();
    }
    return fullText.trim();
  }

  private stripStopTokens(text: string, stopTokens: readonly string[] = ['<|im_end|>', '<|eot_id|>']): string {
    let cleaned = text;
    for (const token of stopTokens) {
      cleaned = cleaned.split(token)[0];
    }
    return cleaned.trim();
  }

  private cleanResponse(response: string, characterName: string, otherCharacterName?: string): string {
    // Remove any character name prefixes that might have been generated
    response = response.replace(new RegExp(`^${characterName}:?\\s*`, 'i'), '');
    if (otherCharacterName) {
      response = response.replace(new RegExp(`^${otherCharacterName}:?\\s*`, 'i'), '');
    }
    
    // Remove any trailing conversation starters or responses
    response = response.replace(/\n.*$/s, ''); // Remove everything after first newline
    
    // Limit length and ensure it ends properly
    response = response.substring(0, 200).trim();
    
    // Ensure it doesn't end mid-sentence
    const sentences = response.split(/[.!?]+/);
    if (sentences.length > 1) {
      sentences.pop(); // Remove potentially incomplete last sentence
      response = sentences.join('.') + '.';
    }
    
    return response || "Hi there!"; // Fallback if response is empty
  }

  isReady(): boolean {
    return this.textGenerator !== null && !this.isLoading;
  }

  getLoadingStatus(): { isLoading: boolean; isReady: boolean; currentModel: string } {
    return {
      isLoading: this.isLoading,
      isReady: this.isReady(),
      currentModel: this.currentModel
    };
  }

  getCurrentModel(): string {
    return this.currentModel;
  }

  getCurrentModelConfig(): ModelConfig | undefined {
    return this.supportedModels[this.currentModel as keyof typeof SUPPORTED_MODELS] as ModelConfig | undefined;
  }

  getSupportedModels(): typeof SUPPORTED_MODELS {
    return this.supportedModels;
  }

  isCloudFallbackAvailable(): boolean {
    return openRouterLLMService.isConfigured();
  }

  async switchModel(modelName: string): Promise<void> {
    if (!(modelName in this.supportedModels)) {
      throw new Error(`Unsupported model: ${modelName}`);
    }

    if (this.currentModel === modelName && this.textGenerator) {
      return; // Already using this model
    }

    // Clear current generator and initialize new model
    this.textGenerator?.dispose?.();
    this.textGenerator = null;
    await this.initialize(modelName);
  }

  async getRecommendedModel(): Promise<string> {
    const capabilities = await backendDetector.detectCapabilities();
    const benchmark = await backendDetector.benchmarkFlops();
    
    // Check memory constraints (rough estimates)
    const memoryMB = benchmark.deviceInfo.memory ? 
      Math.round(benchmark.deviceInfo.memory / 1024 / 1024) : 0;

    // More sophisticated model selection based on actual capabilities
    if (capabilities.webgpu && memoryMB > 8000) {
      // High-end device: prefer the reasoning-oriented LiquidAI model.
      console.log('Recommending LiquidAI LFM2.5 Thinking for high-end device with WebGPU');
      return 'LiquidAI/LFM2.5-1.2B-Thinking-ONNX';
    } else if (capabilities.webgpu && memoryMB > 4000) {
      // Mid-range device: prefer the instruction-tuned LiquidAI model.
      console.log('Recommending LiquidAI LFM2.5 Instruct for mid-range device with WebGPU');
      return 'LiquidAI/LFM2.5-1.2B-Instruct-ONNX';
    } else if (capabilities.simd && memoryMB > 2000) {
      // SIMD-capable device: medium model
      console.log('Recommending LaMini-GPT 774M for SIMD-capable device');
      return 'Xenova/LaMini-GPT-774M';
    } else if (capabilities.wasm && memoryMB > 1000) {
      // Standard device: GPT-2
      console.log('Recommending GPT-2 for standard device');
      return 'Xenova/gpt2';
    } else {
      // Very constrained device: smallest model
      console.log('Recommending DistilGPT-2 for constrained device');
      return 'Xenova/distilgpt2';
    }
  }

  private getOpenRouterModelForCurrentModel(): string {
    if (this.currentModel.includes('Thinking')) {
      return LLM_CONFIG.OPENROUTER_THINKING_MODEL;
    }
    return LLM_CONFIG.OPENROUTER_DEFAULT_MODEL;
  }

  // Validate model compatibility before switching
  async validateModelCompatibility(modelName: string): Promise<{ compatible: boolean; reason?: string }> {
    const capabilities = await backendDetector.detectCapabilities();
    const modelConfig = this.supportedModels[modelName as keyof typeof SUPPORTED_MODELS] as ModelConfig | undefined;
    
    if (!modelConfig) {
      return { compatible: false, reason: `Model ${modelName} is not supported` };
    }

    if (modelConfig.requiresWebGPU && !capabilities.webgpu) {
      return { 
        compatible: false, 
        reason: `Model ${modelConfig.name} requires WebGPU but it's not available on this device` 
      };
    }

    // Check rough memory requirements
    const benchmark = await backendDetector.benchmarkFlops();
    const memoryMB = benchmark.deviceInfo.memory ? 
      Math.round(benchmark.deviceInfo.memory / 1024 / 1024) : 0;

    if (modelConfig.name.includes('3B') && memoryMB < 6000) {
      return {
        compatible: false,
        reason: `3B model requires at least 6GB RAM, but device has ~${Math.round(memoryMB/1024)}GB`
      };
    }

    if (modelConfig.name.includes('1B') && memoryMB < 3000) {
      return {
        compatible: false,
        reason: `1B model requires at least 3GB RAM, but device has ~${Math.round(memoryMB/1024)}GB`
      };
    }

    return { compatible: true };
  }
}

// Export singleton instance
export const clientLLM = new ClientLLMService();
