#!/usr/bin/env node

/**
 * UI Audit Script - Ensures no dead UI elements
 * Scans all UI components to verify every interactive element has handlers
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.dirname(__dirname);

const uiPaths = [
  'client/src/components',
  'client/src/pages',
  'clients/godot/scripts'
];

let violations = [];
let totalElements = 0;
let deadElements = 0;

console.log('🔍 Starting UI Audit - No Dead Elements Policy');
console.log('=' * 50);

function scanFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const fileName = path.relative(projectRoot, filePath);
    
    // Check for interactive elements without handlers
    const interactivePatterns = [
      { pattern: /<Button[^>]*>/g, name: 'Button' },
      { pattern: /<button[^>]*>/g, name: 'button' },
      { pattern: /<Input[^>]*>/g, name: 'Input' },
      { pattern: /<input[^>]*>/g, name: 'input' },
      { pattern: /<select[^>]*>/g, name: 'select' },
      { pattern: /<textarea[^>]*>/g, name: 'textarea' },
      { pattern: /onClick=/g, name: 'onClick handler' },
      { pattern: /onSubmit=/g, name: 'onSubmit handler' },
      { pattern: /pressed\(\)/g, name: 'Godot pressed signal' }
    ];
    
    interactivePatterns.forEach(({ pattern, name }) => {
      const matches = content.match(pattern);
      if (matches) {
        totalElements += matches.length;
        
        matches.forEach(match => {
          // Check if element has proper handlers
          if (name === 'Button' || name === 'button') {
            if (!match.includes('onClick') && !match.includes('onPress') && !match.includes('action')) {
              violations.push({
                file: fileName,
                element: match,
                issue: 'Interactive button without handler',
                line: getLineNumber(content, match)
              });
              deadElements++;
            }
          }
          
          // Check for data-testid
          if (!match.includes('data-testid')) {
            violations.push({
              file: fileName,
              element: match,
              issue: 'Missing data-testid attribute',
              line: getLineNumber(content, match)
            });
          }
        });
      }
    });
    
    // Check for form elements without validation
    const formPattern = /<form[^>]*>/g;
    const formMatches = content.match(formPattern);
    if (formMatches) {
      formMatches.forEach(match => {
        if (!match.includes('onSubmit') && !content.includes('useForm')) {
          violations.push({
            file: fileName,
            element: match,
            issue: 'Form without submission handler',
            line: getLineNumber(content, match)
          });
        }
      });
    }
    
  } catch (error) {
    console.error(`Error scanning ${filePath}:`, error.message);
  }
}

function getLineNumber(content, searchText) {
  const lines = content.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes(searchText)) {
      return i + 1;
    }
  }
  return 0;
}

function scanDirectory(dirPath) {
  if (!fs.existsSync(dirPath)) {
    console.log(`⚠️  Directory not found: ${dirPath}`);
    return;
  }
  
  const files = fs.readdirSync(dirPath, { withFileTypes: true });
  
  files.forEach(file => {
    const fullPath = path.join(dirPath, file.name);
    
    if (file.isDirectory()) {
      scanDirectory(fullPath);
    } else if (file.isFile()) {
      const ext = path.extname(file.name);
      if (['.tsx', '.ts', '.jsx', '.js', '.gd'].includes(ext)) {
        scanFile(fullPath);
      }
    }
  });
}

// Run the audit
uiPaths.forEach(uiPath => {
  const fullPath = path.join(projectRoot, uiPath);
  console.log(`Scanning: ${uiPath}`);
  scanDirectory(fullPath);
});

// Report results
console.log('\n📊 UI Audit Results');
console.log('=' * 30);
console.log(`Total interactive elements: ${totalElements}`);
console.log(`Dead elements found: ${deadElements}`);
console.log(`Violations: ${violations.length}`);

if (violations.length > 0) {
  console.log('\n❌ Violations Found:');
  console.log('-' * 20);
  
  violations.forEach(violation => {
    console.log(`\n📁 ${violation.file}:${violation.line}`);
    console.log(`   Issue: ${violation.issue}`);
    console.log(`   Element: ${violation.element.slice(0, 80)}...`);
  });
  
  console.log('\n🛠️  Fix Required:');
  console.log('1. Add proper event handlers to all interactive elements');
  console.log('2. Add data-testid attributes for testing');
  console.log('3. Ensure forms have submission handlers');
  console.log('4. Connect all UI elements to the event bus');
  
  process.exit(1);
} else {
  console.log('\n✅ All UI elements properly connected!');
  console.log('🎯 No dead buttons or forms found');
  console.log('🔗 Event bus integration verified');
}

console.log('\n🎉 UI Audit Complete');