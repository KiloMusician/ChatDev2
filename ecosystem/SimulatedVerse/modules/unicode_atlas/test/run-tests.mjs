#!/usr/bin/env node
import { strict as assert } from "node:assert";
import { zalgoSafe, stripCombining } from "../lib/zalgo.mjs";
import { readFileSync, existsSync } from "node:fs";

(function testZalgo(){
  const z = zalgoSafe("Test", "readable");
  assert.equal(stripCombining(z), "Test");
  console.log("✅ Zalgo safe/strip test passed");
})();

(function testAtlas(){
  if (!existsSync("assets/unicode/atlas.json")) {
    console.log("⚠️ Atlas not found, run npm run unicode:build first");
    return;
  }
  const atlas = JSON.parse(readFileSync("assets/unicode/atlas.json","utf8"));
  assert.ok(atlas.count > 1000, "Atlas should contain many codepoints");
  console.log("✅ Atlas basic sanity OK");
})();

console.log("🧪 All Unicode tests passed!");