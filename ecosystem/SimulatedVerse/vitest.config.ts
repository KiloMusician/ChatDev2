import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: [
      "tests/**/*.spec.ts",
      "tests/**/*.test.ts",
      "test/**/*.spec.ts",
      "test/**/*.test.ts"
    ],
    exclude: [
      "tests/smoke*.spec.ts",
      "tests/smoke/**",
      "tests/smokes/**",
      "**/node_modules/**",
      "**/dist/**"
    ]
  }
});
