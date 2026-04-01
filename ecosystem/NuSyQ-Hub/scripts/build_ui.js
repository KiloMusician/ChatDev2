#!/usr/bin/env node
/**
 * Minimal UI build runner for NuSyQ.
 * Attempts to run `npm run build` in web/ if package.json exists.
 * Prints clear guidance if Node/npm or the project is missing.
 */

const { execSync } = require("child_process");
const { existsSync } = require("fs");
const { join } = require("path");

function main() {
  const root = process.cwd();
  const webDir = existsSync(join(root, "web")) ? join(root, "web") : root;
  const pkg = join(webDir, "package.json");

  if (!existsSync(pkg)) {
    console.error("No package.json found in web/; skipping UI build.");
    process.exit(0);
  }

  try {
    execSync("npm run build", {
      cwd: webDir,
      stdio: "inherit",
    });
  } catch (err) {
    console.error("UI build failed:", err.message || err);
    process.exit(1);
  }
}

main();
