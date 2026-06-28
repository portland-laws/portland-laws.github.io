const DEFAULT_EMBEDDING_MODEL =
  (import.meta.env.VITE_DEFAULT_EMBEDDING_MODEL as string | undefined) || 'Xenova/gte-small';

interface EmbeddingWorkerData {
  embedding?: number[];
  modelName?: string;
  isInitialized?: boolean;
  attemptedModels?: string[];
  failedAttempts?: string[];
}

interface PendingRequest {
  resolve: (value: EmbeddingWorkerData) => void;
  reject: (reason?: any) => void;
}

class ClientEmbeddingWorkerService {
  private worker: Worker | null = null;
  private requestCounter = 0;
  private pendingRequests = new Map<string, PendingRequest>();
  private currentModel = DEFAULT_EMBEDDING_MODEL;

  constructor() {
    this.initializeWorker();
  }

  private initializeWorker() {
    try {
      this.worker?.terminate();
      this.worker = new Worker(new URL('../workers/embeddingWorker.ts', import.meta.url), {
        type: 'module',
      });
      this.worker.onmessage = this.handleWorkerMessage.bind(this);
      this.worker.onerror = this.handleWorkerError.bind(this);
    } catch (error) {
      console.error('Failed to create embedding worker:', error);
      this.worker = null;
    }
  }

  private handleWorkerMessage(event: MessageEvent) {
    const { id, success, data, error } = event.data;
    const pending = this.pendingRequests.get(id);
    if (!pending) {
      return;
    }

    this.pendingRequests.delete(id);
    if (success) {
      if (data?.modelName) {
        this.currentModel = data.modelName;
      }
      pending.resolve(data);
    } else {
      pending.reject(new Error(error || 'Embedding worker request failed'));
      this.resetWorkerAfterRuntimeFailure(error);
    }
  }

  private handleWorkerError(error: ErrorEvent) {
    console.error('Embedding worker error:', error);
    for (const [id, pending] of this.pendingRequests.entries()) {
      pending.reject(new Error('Embedding worker error'));
      this.pendingRequests.delete(id);
    }
    this.resetWorker();
  }

  private resetWorkerAfterRuntimeFailure(error?: string) {
    if (!error || !error.includes('byteLength')) {
      return;
    }
    this.resetWorker();
  }

  private resetWorker() {
    this.worker?.terminate();
    this.worker = null;
    this.initializeWorker();
  }

  private sendWorkerRequest(type: string, data: unknown, timeoutMs = 90000): Promise<EmbeddingWorkerData> {
    if (!this.worker) {
      this.initializeWorker();
    }

    if (!this.worker) {
      throw new Error('Embedding worker is not available');
    }
    const worker = this.worker;

    return new Promise((resolve, reject) => {
      const id = `embedding_${++this.requestCounter}`;
      const timeout = window.setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error('Embedding worker request timed out'));
        }
      }, timeoutMs);

      this.pendingRequests.set(id, {
        resolve: (value) => {
          window.clearTimeout(timeout);
          resolve(value);
        },
        reject: (reason) => {
          window.clearTimeout(timeout);
          reject(reason);
        },
      });

      worker.postMessage({ id, type, data });
    });
  }

  async generateEmbedding(text: string, modelName = this.currentModel): Promise<Float32Array> {
    const response = await this.sendWorkerRequest('embed', { text, modelName });
    if (!Array.isArray(response.embedding) || response.embedding.length === 0) {
      throw new Error('Embedding worker returned an invalid embedding');
    }

    const embedding = new Float32Array(response.embedding);
    const invalidIndex = embedding.findIndex((value) => !Number.isFinite(value));
    if (invalidIndex !== -1) {
      throw new Error(`Embedding worker returned a non-finite value at index ${invalidIndex}`);
    }

    if (response.modelName) {
      this.currentModel = response.modelName;
    }

    return embedding;
  }

  async getStatus(): Promise<{ modelName: string; isInitialized: boolean }> {
    try {
      const response = await this.sendWorkerRequest('status', {}, 5000);
      return {
        modelName: response.modelName || this.currentModel,
        isInitialized: Boolean(response.isInitialized),
      };
    } catch {
      return { modelName: this.currentModel, isInitialized: false };
    }
  }
}

export const clientEmbeddingWorkerService = new ClientEmbeddingWorkerService();
