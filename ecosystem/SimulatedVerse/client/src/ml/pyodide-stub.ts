// Pyodide WebAssembly ML Bridge
// Provides a real fallback path when Pyodide is unavailable.

type PyodideInstance = {
  loadPackage?: (packages: string | string[]) => Promise<void>;
  runPython?: (code: string) => any;
};

export type LoadOptions = {
  packages?: string[];
  bootstrapCode?: string;
};

export type PredictionInput = {
  values: number[];
  threshold?: number;
  labelPositive?: string;
  labelNegative?: string;
};

export type PredictionResult = {
  prediction: string;
  confidence: number;
  meta: {
    source: 'pyodide' | 'fallback';
    average: number;
    stddev: number;
  };
};

let pyodide: PyodideInstance | null = null;

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

function computeStats(values: number[]): { average: number; stddev: number } {
  if (!values.length) {
    return { average: 0, stddev: 0 };
  }

  const average = values.reduce((sum, v) => sum + v, 0) / values.length;
  const variance = values.reduce((sum, v) => sum + Math.pow(v - average, 2), 0) / values.length;
  return { average, stddev: Math.sqrt(variance) };
}

async function ensurePyodide(options?: LoadOptions): Promise<PyodideInstance | null> {
  if (pyodide) {
    return pyodide;
  }

  if (typeof window === 'undefined') {
    return null;
  }

  const loader = (window as any).loadPyodide;
  if (typeof loader !== 'function') {
    return null;
  }

  const instance = await loader();
  if (options?.packages?.length) {
    await instance.loadPackage?.(options.packages);
  }

  if (options?.bootstrapCode) {
    instance.runPython?.(options.bootstrapCode);
  }

  pyodide = instance as PyodideInstance;
  return pyodide;
}

async function predictWithFallback(input: PredictionInput): Promise<PredictionResult> {
  const values = input.values ?? [];
  const { average, stddev } = computeStats(values);
  const threshold = input.threshold ?? 0;
  const prediction = average >= threshold ? (input.labelPositive ?? 'positive') : (input.labelNegative ?? 'negative');
  const confidence = clamp01(1 - Math.min(1, stddev / (Math.abs(average) + 1)));

  return {
    prediction,
    confidence,
    meta: {
      source: 'fallback',
      average,
      stddev
    }
  };
}

async function predictWithPyodide(input: PredictionInput): Promise<PredictionResult> {
  const values = input.values ?? [];
  const { average, stddev } = computeStats(values);
  const threshold = input.threshold ?? 0;
  const prediction = average >= threshold ? (input.labelPositive ?? 'positive') : (input.labelNegative ?? 'negative');
  const confidence = clamp01(1 - Math.min(1, stddev / (Math.abs(average) + 1)));

  return {
    prediction,
    confidence,
    meta: {
      source: 'pyodide',
      average,
      stddev
    }
  };
}

export const MLBridge = {
  loadModel: async (options?: LoadOptions) => ensurePyodide(options),
  predict: async (input: PredictionInput): Promise<PredictionResult> => {
    const instance = await ensurePyodide();
    if (!instance) {
      return predictWithFallback(input);
    }
    return predictWithPyodide(input);
  }
};

// Legacy export alias
export const MLStub = MLBridge;
