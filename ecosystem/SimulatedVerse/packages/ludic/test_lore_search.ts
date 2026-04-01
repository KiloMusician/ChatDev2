import fs from 'node:fs';
import path from 'node:path';
import { LoreDiscovery } from './lore-discovery';

async function main() {
  // create a temp vault directory with one markdown file
  const tmpVault = path.join(process.cwd(), 'tmp_vault_for_test');
  try {
    if (!fs.existsSync(tmpVault)) fs.mkdirSync(tmpVault, { recursive: true });
    const filePath = path.join(tmpVault, 'Test Discovery.md');
    const content = `# The Great Pattern\n\nThis note contains a unique insight about consciousness and pattern recognition. #consciousness`;
    fs.writeFileSync(filePath, content, 'utf8');

    // instantiate LoreDiscovery pointing at the tmp vault
    const discovery = new LoreDiscovery(tmpVault);
    // perform a search for 'consciousness'
    const results = discovery.searchLore('consciousness', 'test_runner');

    if (results.length === 0) {
      console.error('[test_lore_search] FAILED: expected at least one search result');
      process.exit(2);
    }

    console.log(`[test_lore_search] OK: found ${results.length} entries (top title=${results[0].title})`);
    process.exit(0);
  } catch (e) {
    console.error('[test_lore_search] ERROR', e);
    process.exit(3);
  } finally {
    // cleanup
    try { fs.rmSync(tmpVault, { recursive: true, force: true }); } catch {};
  }
}

main();
