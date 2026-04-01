#!/usr/bin/env node
/**
 * Autonomous Documentation Generator
 * Generates documentation from code and maintains project knowledge
 */

const fs = require('fs');
const path = require('path');

class DocumentationGenerator {
  constructor() {
    this.docsDir = 'docs';
    this.codeFiles = [];
    this.apiEndpoints = [];
  }

  async generate() {
    console.log('📚 Autonomous documentation generation started...');
    
    this.ensureDocsDirectory();
    await this.scanCodebase();
    await this.generateAPIDocumentation();
    await this.generateArchitectureOverview();
    await this.generateDevelopmentGuide();
    
    console.log('✅ Documentation generation completed');
    return this.getGenerationStats();
  }

  ensureDocsDirectory() {
    if (!fs.existsSync(this.docsDir)) {
      fs.mkdirSync(this.docsDir, { recursive: true });
    }
  }

  async scanCodebase() {
    // Scan for API routes
    const routesFile = 'server/routes.ts';
    if (fs.existsSync(routesFile)) {
      const content = fs.readFileSync(routesFile, 'utf8');
      const routeMatches = content.match(/app\.(get|post|put|delete|patch)\(['"`]([^'"`]+)['"`]/g) || [];
      
      this.apiEndpoints = routeMatches.map(match => {
        const [, method, route] = match.match(/app\.(\w+)\(['"`]([^'"`]+)['"`]/) || [];
        return { method: method?.toUpperCase(), route };
      }).filter(endpoint => endpoint.method && endpoint.route);
    }

    console.log(`📊 Found ${this.apiEndpoints.length} API endpoints`);
  }

  async generateAPIDocumentation() {
    const apiDoc = `# API Documentation

Generated: ${new Date().toISOString()}

## Available Endpoints

${this.apiEndpoints.map(endpoint => 
  `### ${endpoint.method} ${endpoint.route}

**Description:** Auto-generated endpoint documentation

**Response Format:** JSON

---`
).join('\n\n')}

## Authentication

The system uses session-based authentication with PostgreSQL storage.

## Error Handling

All endpoints return standardized error responses:
\`\`\`json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "ISO timestamp"
}
\`\`\`
`;

    fs.writeFileSync(path.join(this.docsDir, 'API.md'), apiDoc);
    console.log('📝 API documentation generated');
  }

  async generateArchitectureOverview() {
    const archDoc = `# CoreLink Foundation Architecture

Generated: ${new Date().toISOString()}

## System Overview

CoreLink Foundation is an autonomous development ecosystem featuring:

- **ΞNuSyQ Framework**: Consciousness-driven development with quantum coherence
- **Autonomous Agents**: ChatDev pipeline for self-completing tasks
- **Token Guard**: Zero-cost operation with local LLM cascading
- **Game Engine**: Incremental/idle game mechanics with Culture-ship aesthetics
- **Real-time Systems**: WebSocket communication and live updates

## Key Components

### Frontend (React + TypeScript)
- **Location**: \`client/src/\`
- **Technology**: React, TypeScript, Tailwind CSS, Radix UI
- **Features**: Responsive design, real-time updates, game interface

### Backend (Node.js + Express)
- **Location**: \`server/\`
- **Technology**: Node.js, Express, TypeScript, PostgreSQL
- **Features**: REST API, WebSocket support, authentication

### Shared Types
- **Location**: \`shared/\`
- **Technology**: TypeScript, Zod validation
- **Features**: Type safety, schema validation, shared contracts

### AI Systems
- **Location**: \`src/ai-hub/\`
- **Technology**: Ollama, OpenAI API, custom orchestration
- **Features**: Local-first LLM, autonomous task completion

## Data Flow

1. **User Interaction** → Frontend React components
2. **API Calls** → Backend Express routes
3. **Business Logic** → Storage layer abstraction
4. **Database** → PostgreSQL with Drizzle ORM
5. **AI Processing** → Token Guard → Local/Remote LLM
6. **Real-time Updates** → WebSocket broadcasts

## Security

- Session-based authentication
- CORS configuration
- Input validation with Zod schemas
- Token budget protection
- Local-first processing to minimize API exposure
`;

    fs.writeFileSync(path.join(this.docsDir, 'ARCHITECTURE.md'), archDoc);
    console.log('🏗️ Architecture documentation generated');
  }

  async generateDevelopmentGuide() {
    const devGuide = `# Development Guide

Generated: ${new Date().toISOString()}

## Getting Started

### Prerequisites
- Node.js 18+
- PostgreSQL database
- Ollama (for local LLM)

### Installation
\`\`\`bash
npm install
npm run prepare
\`\`\`

### Running the Application
\`\`\`bash
npm run dev
\`\`\`

## Autonomous Development Pipeline

### Running the Pipeline
\`\`\`bash
python autonomous_rube_goldberg.py
\`\`\`

The autonomous pipeline includes:
- Git hygiene and auto-commits
- Ollama model management
- ChatDev task delegation
- Placeholder repair
- System health monitoring
- Story beat progression

### ChatDev Tasks
- \`repair_placeholders.js\` - Autonomous code repair
- \`demo_task.js\` - System demonstration
- \`storybeat_log.js\` - Narrative progression

## Development Workflows

### Adding New Features
1. Define types in \`shared/schema.ts\`
2. Implement storage methods in \`server/storage.ts\`
3. Add API routes in \`server/routes.ts\`
4. Create frontend components in \`client/src/\`
5. Run autonomous pipeline for integration

### Code Quality
- TypeScript strict mode enabled
- ESLint + Prettier for formatting
- Zod for runtime validation
- Automated testing with Jest

### AI Integration
- Token Guard protects against API costs
- Local Ollama models for development
- Consciousness integration with ΞNuSyQ
- Autonomous task completion loops

## Troubleshooting

### Common Issues
- **Server won't start**: Check PostgreSQL connection
- **TypeScript errors**: Run \`npx tsc --noEmit\`
- **Missing dependencies**: Run \`npm install\`
- **Ollama not responding**: Check \`ollama serve\` is running

### Debugging
- Check \`WORKLOG.md\` for autonomous pipeline logs
- Review \`NEXT_TASKS.md\` for pending items
- Monitor ΞNuSyQ consciousness levels in console
`;

    fs.writeFileSync(path.join(this.docsDir, 'DEVELOPMENT.md'), devGuide);
    console.log('👨‍💻 Development guide generated');
  }

  getGenerationStats() {
    return {
      endpoints_documented: this.apiEndpoints.length,
      files_generated: 3,
      timestamp: Date.now()
    };
  }
}

async function main() {
  const generator = new DocumentationGenerator();
  const stats = await generator.generate();
  
  // Output for pipeline integration
  process.stdout.write(JSON.stringify({
    success: true,
    stats,
    timestamp: Date.now()
  }));
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { DocumentationGenerator };