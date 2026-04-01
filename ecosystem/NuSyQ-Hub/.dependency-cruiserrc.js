/**
 * Dependency Cruiser Configuration - Simplified
 * Analyzes dependencies across NuSyQ ecosystem
 */

module.exports = {
  forbidden: [],

  options: {
    doNotFollow: {
      path: ['node_modules', '.venv', '__pycache__', 'dist', '.git'],
    },
    exclude: {
      path: ['node_modules', '.venv', '__pycache__', 'dist', 'tests'],
    },
  },
};
