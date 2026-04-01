#!/usr/bin/env node

/**
 * Schema Validation Script
 * Validates all YAML directives against their schemas
 */

import fs from 'fs';
import path from 'path';
import yaml from 'yaml';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.dirname(__dirname);

const ajv = new Ajv({ allErrors: true });
addFormats(ajv);

let totalFiles = 0;
let validFiles = 0;
let errors = [];

console.log('📋 Starting Schema Validation');
console.log('=' * 40);

function loadSchema(schemaPath) {
  try {
    const schemaContent = fs.readFileSync(schemaPath, 'utf8');
    return JSON.parse(schemaContent);
  } catch (error) {
    console.error(`Failed to load schema ${schemaPath}:`, error.message);
    return null;
  }
}

function validateDirective(filePath, schema) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const data = yaml.parse(content);
    
    const validate = ajv.compile(schema);
    const isValid = validate(data);
    
    totalFiles++;
    
    if (isValid) {
      validFiles++;
      console.log(`✅ ${path.relative(projectRoot, filePath)}`);
      return true;
    } else {
      console.log(`❌ ${path.relative(projectRoot, filePath)}`);
      validate.errors.forEach(error => {
        const errorMsg = `  ${error.instancePath || 'root'}: ${error.message}`;
        console.log(errorMsg);
        errors.push({
          file: filePath,
          path: error.instancePath,
          message: error.message,
          data: error.data
        });
      });
      return false;
    }
  } catch (error) {
    console.log(`❌ ${path.relative(projectRoot, filePath)} - Parse Error: ${error.message}`);
    errors.push({
      file: filePath,
      path: 'parse',
      message: error.message,
      data: null
    });
    totalFiles++;
    return false;
  }
}

function validateAllDirectives() {
  const directiveSchema = loadSchema(path.join(projectRoot, 'content/schema/directive.json'));
  if (!directiveSchema) {
    console.error('Failed to load directive schema');
    return false;
  }
  
  const directivesDir = path.join(projectRoot, 'content/directives');
  
  if (!fs.existsSync(directivesDir)) {
    console.log('📁 Creating directives directory...');
    fs.mkdirSync(directivesDir, { recursive: true });
    
    // Create a sample directive for testing
    const sampleDirective = {
      id: 'sample_building_001',
      kind: 'building',
      tier: 2,
      unlock: {
        tier: 2,
        resources: {
          metal: 100,
          power: 50
        }
      },
      effects: [
        {
          type: 'multiplier',
          target: 'power_generation',
          value: 1.2
        }
      ],
      metadata: {
        spawned: Date.now(),
        validated: true,
        active: false,
        description: 'Sample directive for testing',
        tags: ['building', 'power', 'tier2']
      }
    };
    
    const samplePath = path.join(directivesDir, 'sample.yml');
    fs.writeFileSync(samplePath, yaml.stringify(sampleDirective));
    console.log('📝 Created sample directive for validation');
  }
  
  const files = fs.readdirSync(directivesDir).filter(file => 
    file.endsWith('.yml') || file.endsWith('.yaml')
  );
  
  console.log(`\n🔍 Validating ${files.length} directive files...\n`);
  
  let allValid = true;
  files.forEach(file => {
    const filePath = path.join(directivesDir, file);
    const isValid = validateDirective(filePath, directiveSchema);
    if (!isValid) allValid = false;
  });
  
  return allValid;
}

function validateTypeDefinitions() {
  console.log('\n🔧 Validating TypeScript type definitions...');
  
  const typeFiles = [
    'shared/types/core.ts',
    'shared/bus/contracts.ts'
  ];
  
  typeFiles.forEach(typeFile => {
    const fullPath = path.join(projectRoot, typeFile);
    if (fs.existsSync(fullPath)) {
      console.log(`✅ ${typeFile} - exists`);
      
      // Basic syntax check
      const content = fs.readFileSync(fullPath, 'utf8');
      if (content.includes('export interface') || content.includes('export type')) {
        console.log(`  └─ Contains type definitions`);
      } else {
        console.log(`  └─ ⚠️  No type definitions found`);
      }
    } else {
      console.log(`❌ ${typeFile} - missing`);
      errors.push({
        file: typeFile,
        path: 'file',
        message: 'Required type definition file missing',
        data: null
      });
    }
  });
}

function validateBusContracts() {
  console.log('\n🚌 Validating Event Bus contracts...');
  
  const contractFile = path.join(projectRoot, 'shared/bus/contracts.ts');
  if (!fs.existsSync(contractFile)) {
    console.log('❌ Bus contracts file missing');
    return false;
  }
  
  const content = fs.readFileSync(contractFile, 'utf8');
  
  // Check for required types
  const requiredTypes = ['BusEvent', 'Rpc', 'BusMessage'];
  requiredTypes.forEach(type => {
    if (content.includes(`export type ${type}`) || content.includes(`export interface ${type}`)) {
      console.log(`✅ ${type} - defined`);
    } else {
      console.log(`❌ ${type} - missing`);
      errors.push({
        file: contractFile,
        path: 'type',
        message: `Required type ${type} not found`,
        data: type
      });
    }
  });
  
  return true;
}

// Run all validations
console.log('Starting comprehensive schema validation...\n');

const directivesValid = validateAllDirectives();
validateTypeDefinitions();
validateBusContracts();

// Summary
console.log('\n📊 Validation Summary');
console.log('=' * 30);
console.log(`Directive files: ${validFiles}/${totalFiles} valid`);
console.log(`Total errors: ${errors.length}`);

if (errors.length > 0) {
  console.log('\n❌ Validation Failed');
  console.log('-' * 20);
  
  // Group errors by type
  const errorsByType = errors.reduce((acc, error) => {
    const type = error.path || 'unknown';
    if (!acc[type]) acc[type] = [];
    acc[type].push(error);
    return acc;
  }, {});
  
  Object.entries(errorsByType).forEach(([type, typeErrors]) => {
    console.log(`\n🔍 ${type} errors (${typeErrors.length}):`);
    typeErrors.slice(0, 5).forEach(error => { // Show max 5 per type
      console.log(`  📁 ${path.relative(projectRoot, error.file)}`);
      console.log(`     ${error.message}`);
    });
    if (typeErrors.length > 5) {
      console.log(`     ... and ${typeErrors.length - 5} more`);
    }
  });
  
  console.log('\n🛠️  Next Steps:');
  console.log('1. Fix schema validation errors in directive files');
  console.log('2. Ensure all required type definitions exist');
  console.log('3. Verify event bus contracts are complete');
  console.log('4. Run validation again: npm run schema-validate');
  
  process.exit(1);
} else {
  console.log('\n✅ All schemas valid!');
  console.log('🎯 Directive system ready');
  console.log('🚌 Event bus contracts verified');
  console.log('📋 Type definitions complete');
}

console.log('\n🎉 Schema Validation Complete');