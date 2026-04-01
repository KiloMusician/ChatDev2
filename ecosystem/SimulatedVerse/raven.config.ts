/**
 * Raven Configuration
 * Models, context windows, budgets, routing rules
 */

export interface LLMModelConfig {
  name: string;
  provider: 'ollama' | 'openai' | 'anthropic';
  endpoint?: string;
  max_tokens: number;
  context_window: number;
  cost_per_token?: number;
  capabilities: string[];
}

export interface RavenBudgetConfig {
  daily_allowance: number;
  per_pr_cap: number;
  warn_threshold: number; // 70%
  hard_threshold: number; // 90%
  emergency_reserve: number;
}

export interface RavenPolicyConfig {
  max_pr_size: number;
  max_file_changes: number;
  require_tests: boolean;
  require_artifacts: boolean;
  forbidden_paths: string[];
  branch_protection: boolean;
}

export interface RavenMemoryConfig {
  vector_store: 'sqlite' | 'faiss' | 'chroma';
  embedding_model: string;
  cache_ttl: number;
  max_episodic_items: number;
  semantic_similarity_threshold: number;
}

export interface RavenSkillsConfig {
  enabled_skills: string[];
  skill_weights: Record<string, number>;
  git_config: {
    default_branch: string;
    pr_template_path: string;
    auto_merge_labels: string[];
  };
  test_config: {
    timeout: number;
    coverage_threshold: number;
    frameworks: string[];
  };
}

export interface RavenAdapterConfig {
  llm_routing: {
    planning: string;
    implementation: string;
    reflection: string;
    analysis: string;
  };
  fallback_enabled: boolean;
  local_first: boolean;
  retry_config: {
    max_retries: number;
    backoff_ms: number;
  };
}

export interface RavenConfig {
  models: LLMModelConfig[];
  budget: RavenBudgetConfig;
  policy: RavenPolicyConfig;
  memory: RavenMemoryConfig;
  skills: RavenSkillsConfig;
  adapters: RavenAdapterConfig;
  infrastructure: {
    enabled: boolean;
    admin_token_required: boolean;
    kill_switch_enabled: boolean;
    entropy_throttling: boolean;
    no_lies_verification: boolean;
  };
}

// Default configuration - infrastructure-first, local-first, strict discipline
export const DEFAULT_RAVEN_CONFIG: RavenConfig = {
  models: [
    {
      name: 'qwen2.5:7b',
      provider: 'ollama',
      endpoint: 'http://localhost:11434',
      max_tokens: 4096,
      context_window: 32768,
      capabilities: ['planning', 'implementation', 'analysis']
    },
    {
      name: 'llama3.1:8b',
      provider: 'ollama',
      endpoint: 'http://localhost:11434',
      max_tokens: 4096,
      context_window: 128000,
      capabilities: ['reflection', 'documentation']
    },
    {
      name: 'phi3:mini',
      provider: 'ollama',
      endpoint: 'http://localhost:11434',
      max_tokens: 2048,
      context_window: 4096,
      capabilities: ['quick_tasks', 'validation']
    },
    {
      name: 'gpt-4o-mini',
      provider: 'openai',
      max_tokens: 16384,
      context_window: 128000,
      cost_per_token: 0.00015,
      capabilities: ['fallback', 'complex_planning']
    }
  ],
  
  budget: {
    daily_allowance: 100, // tokens or cost units
    per_pr_cap: 10,
    warn_threshold: 0.7,
    hard_threshold: 0.9,
    emergency_reserve: 20
  },
  
  policy: {
    max_pr_size: 500, // lines
    max_file_changes: 10,
    require_tests: true,
    require_artifacts: true,
    forbidden_paths: [
      'server/db/',
      'shared/schema.ts',
      'package.json',
      '.env*'
    ],
    branch_protection: true
  },
  
  memory: {
    vector_store: 'sqlite',
    embedding_model: 'all-MiniLM-L6-v2',
    cache_ttl: 86400000, // 24 hours
    max_episodic_items: 1000,
    semantic_similarity_threshold: 0.8
  },
  
  skills: {
    enabled_skills: [
      'git', 'test', 'refactor', 'document', 
      'analyze', 'balance', 'simulate'
    ],
    skill_weights: {
      'git': 1.0,
      'test': 0.9,
      'refactor': 0.8,
      'document': 0.7,
      'analyze': 0.9,
      'balance': 0.6,
      'simulate': 0.5
    },
    git_config: {
      default_branch: 'main',
      pr_template_path: '.github/pull_request_template.md',
      auto_merge_labels: ['automerge:candidate', 'agent:raven']
    },
    test_config: {
      timeout: 30000,
      coverage_threshold: 0.8,
      frameworks: ['jest', 'vitest', 'cypress']
    }
  },
  
  adapters: {
    llm_routing: {
      planning: 'qwen2.5:7b',
      implementation: 'llama3.1:8b', 
      reflection: 'phi3:mini',
      analysis: 'qwen2.5:7b'
    },
    fallback_enabled: false, // Start with local-only
    local_first: true,
    retry_config: {
      max_retries: 3,
      backoff_ms: 1000
    }
  },
  
  infrastructure: {
    enabled: false, // Require explicit enablement
    admin_token_required: true,
    kill_switch_enabled: true,
    entropy_throttling: true,
    no_lies_verification: true
  }
};

export function loadRavenConfig(overrides: Partial<RavenConfig> = {}): RavenConfig {
  return {
    ...DEFAULT_RAVEN_CONFIG,
    ...overrides,
    models: overrides.models || DEFAULT_RAVEN_CONFIG.models,
    budget: { ...DEFAULT_RAVEN_CONFIG.budget, ...overrides.budget },
    policy: { ...DEFAULT_RAVEN_CONFIG.policy, ...overrides.policy },
    memory: { ...DEFAULT_RAVEN_CONFIG.memory, ...overrides.memory },
    skills: { ...DEFAULT_RAVEN_CONFIG.skills, ...overrides.skills },
    adapters: { ...DEFAULT_RAVEN_CONFIG.adapters, ...overrides.adapters },
    infrastructure: { ...DEFAULT_RAVEN_CONFIG.infrastructure, ...overrides.infrastructure }
  };
}