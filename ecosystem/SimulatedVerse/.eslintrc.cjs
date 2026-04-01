module.exports = {
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: './tsconfig.json',
  },
  plugins: ['@typescript-eslint'],
  rules: {
    // Only break CI on syntax errors, not style issues
    '@typescript-eslint/no-unused-vars': 'warn',
    '@typescript-eslint/no-explicit-any': 'warn',
    'no-console': 'warn',
    'no-debugger': 'error',
    'no-unreachable': 'error',
    
    // Culture Mind Ethics - be permissive but helpful
    '@typescript-eslint/no-non-null-assertion': 'warn',
    '@typescript-eslint/prefer-optional-chain': 'warn',
    '@typescript-eslint/no-unsafe-argument': 'warn',
    
    // Map safety rules - prevent "m.map is not a function" errors
    'no-restricted-syntax': [
      'warn',
      {
        selector: 'CallExpression[callee.property.name="map"]',
        message: 'Use safeMap/normalizeToArray for unknown sources',
      },
    ],
    
    // Allow flexible patterns for rapid development
    '@typescript-eslint/ban-ts-comment': 'off',
    '@typescript-eslint/no-empty-function': 'warn',
  },
  ignorePatterns: [
    'node_modules/',
    'dist/',
    'build/',
    '*.js',
    '.cache/',
    'attached_assets/',
  ],
};