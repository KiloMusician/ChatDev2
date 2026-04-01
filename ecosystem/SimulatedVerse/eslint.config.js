// ESLint v9 flat config — migrated from .eslintrc.cjs (2026-03-02)
import tseslint from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';

// Honor .eslintignore patterns as flat-config ignores
const ignores = [
  'node_modules/**', 'dist/**', 'build/**', 'coverage/**',
  'reports/**', 'attic/**', '**/*.js', '.cache/**', 'attached_assets/**',
];

// Shared rule set — permissive for rapid ecosystem dev
const permissiveRules = {
  ...tseslint.configs.recommended.rules,
  '@typescript-eslint/no-unused-vars': ['warn', { caughtErrors: 'none', argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
  '@typescript-eslint/no-explicit-any': 'warn',
  // Allow semantic console levels (error/warn/info/debug); flag raw console.log
  'no-console': ['warn', { allow: ['error', 'warn', 'info', 'debug', 'trace'] }],
  'no-debugger': 'error',
  'no-unreachable': 'error',
  '@typescript-eslint/no-non-null-assertion': 'warn',
  '@typescript-eslint/no-empty-function': 'warn',
  '@typescript-eslint/ban-ts-comment': 'off',
  '@typescript-eslint/no-unsafe-argument': 'off',
  '@typescript-eslint/no-unsafe-assignment': 'off',
  '@typescript-eslint/no-unsafe-member-access': 'off',
  '@typescript-eslint/no-unsafe-call': 'off',
  '@typescript-eslint/no-unsafe-return': 'off',
  '@typescript-eslint/no-unsafe-function-type': 'warn',
  '@typescript-eslint/no-require-imports': 'warn',
  '@typescript-eslint/no-unused-expressions': 'warn',
  '@typescript-eslint/no-empty-object-type': 'warn',
};

const globals = { console: true, process: true, Buffer: true, __dirname: true, __filename: true, setTimeout: true, setInterval: true, clearTimeout: true, clearInterval: true, fetch: true, window: true, document: true };

export default [
  { ignores },
  // Server — type-aware linting with root tsconfig
  {
    files: ['server/**/*.ts', 'shared/**/*.ts', 'ops/**/*.ts', 'modules/**/*.ts'],
    plugins: { '@typescript-eslint': tseslint },
    languageOptions: {
      parser: tsParser,
      parserOptions: { ecmaVersion: 'latest', sourceType: 'module', project: './tsconfig.json' },
      globals,
    },
    rules: permissiveRules,
  },
  // Client — no type-aware project (client has its own tsconfig)
  {
    files: ['client/**/*.ts', 'client/**/*.tsx'],
    plugins: { '@typescript-eslint': tseslint },
    languageOptions: {
      parser: tsParser,
      parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
      globals,
    },
    rules: permissiveRules,
  },
];
