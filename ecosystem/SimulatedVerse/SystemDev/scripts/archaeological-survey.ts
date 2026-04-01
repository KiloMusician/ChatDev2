#!/usr/bin/env tsx
/**
 * SCP FOUNDATION - MOBILE TASK FORCE DELTA-7
 * ARCHAEOLOGICAL SURVEY COMMAND
 * 
 * MISSION: Execute site-wide survey and generate containment reports
 */

import { RosettaStone } from '../src/infra/rosetta-stone';

async function main() {
  console.log('🚨 SCP FOUNDATION - MOBILE TASK FORCE DELTA-7');
  console.log('📋 INITIATING ARCHAEOLOGICAL SURVEY');
  console.log('🔍 Operation: Systematic Cartography & Integration');
  console.log('');
  
  const rosetta = new RosettaStone();
  
  try {
    const results = await rosetta.catalogEntireSite();
    
    console.log('');
    console.log('✅ ARCHAEOLOGICAL SURVEY COMPLETE');
    console.log('📊 FINAL STATISTICS:');
    console.log(`   - Total Artifacts: ${results.statistics.total_files}`);
    console.log(`   - High-Risk Entities: ${results.statistics.high_risk_count}`);
    console.log(`   - Duplicate Instances: ${results.statistics.total_duplicates}`);
    console.log('');
    console.log('📋 OBJECT CLASS DISTRIBUTION:');
    Object.entries(results.statistics.by_object_class).forEach(([cls, count]) => {
      console.log(`   - ${cls}: ${count} artifacts`);
    });
    console.log('');
    console.log('🗂️ Reports generated in site-manifest/');
    console.log('🔒 All artifacts contained and classified');
    
    // Identify containment breaches
    const keterEntities = results.manifests.filter(m => m.object_class === 'KETER');
    if (keterEntities.length > 0) {
      console.log('');
      console.log('🚨 KETER-CLASS ENTITIES REQUIRING IMMEDIATE ATTENTION:');
      keterEntities.forEach(entity => {
        console.log(`   - ${entity.scp_id}: ${entity.original_path} (Risk: ${entity.risk_level.toFixed(2)})`);
      });
    }
    
  } catch (error) {
    console.error('💥 SURVEY FAILED:', error);
    process.exit(1);
  }
}

// ES Module compatible entry point
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}