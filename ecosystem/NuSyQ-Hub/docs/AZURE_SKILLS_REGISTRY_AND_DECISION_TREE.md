# 🎯 Master Azure Skills Registry & Decision Tree
**Date:** 2026-02-28  
**Version:** 1.0  
**Purpose:** Single authoritative reference for all 21 Azure skills

---

## Quick Reference: Which Skill to Use?

### 🟢 **I'm starting a new project or adding features to an app**
→ **Use `azure-prepare`** (default entry point)

### 🟢 **I'm deploying to Azure**
→ **Use `azure-deploy`** (after validate)

### 🟢 **I want to check if my app is ready to deploy**
→ **Use `azure-validate`** (required before deploy)

### 🟡 **I need to understand Azure costs**
→ **Use `azure-cost-optimization`**

### 🟡 **My app stops working in Azure**
→ **Use `azure-diagnostics`**

### 🟡 **I need to check compliance/security**
→ **Use `azure-compliance`**

### 🟡 **I'm moving from AWS/GCP to Azure**
→ **Use `azure-cloud-migrate`**

### 🔵 **I'm building something specific:**

| What you're building | Use this skill |
|---|---|
| Copilot-powered app | `azure-hosted-copilot-sdk` |
| AI Search / Vector DB / RAG | `azure-ai` |
| Speech-to-text / Text-to-speech | `azure-ai` |
| API with governance / caching | `azure-aigateway` |
| Choosing VM size | `azure-compute` |
| App Insights / Monitoring | `azure-observability` |
| Application logs / KQL queries | `azure-observability` |
| Kusto/Data Explorer queries | `azure-kusto` |
| Blob Storage / File Shares | `azure-storage` |
| Event Hubs / Service Bus | `azure-messaging` |
| Role / Permission assignment | `azure-rbac` |
| Troubleshooting container apps | `azure-diagnostics` |
| Listing my Azure resources | `azure-resource-lookup` |
| Drawing architecture diagram | `azure-resource-visualizer` |

---

## 📋 Complete Skill Inventory

### **Entry Points (Start Here)**

#### 1. **azure-prepare** ⭐ DEFAULT
```
WHEN: "create an app", "build web app", "set up Azure", "modernize code"
WORKFLOW: Plan → Research → Generate → Harden → Validate (then use azure-deploy)
OUTPUT: .azure/plan.md, Bicep/Terraform, azure.yaml, Dockerfile
PREREQUISITE: None (this is the entry point)
NEXT: azure-validate, then azure-deploy
```

#### 2. **azure-deploy** ⭐ DEPLOYMENT
```
WHEN: "deploy to Azure", "run azd up", "push to cloud", "go live"
WORKFLOW: Check plan → Pre-flight → Execute → Verify
OUTPUT: Running service on Azure
PREREQUISITE: .azure/plan.md with status=Validated (from azure-validate)
NEXT: azure-diagnostics if issues occur
```

#### 3. **azure-validate** ⭐ PRE-DEPLOYMENT
```
WHEN: "check if ready to deploy", "validate my config", "preflight check"
WORKFLOW: Deep checks on config, permissions, prerequisites
OUTPUT: Plan status = Validated
PREREQUISITE: .azure/plan.md (from azure-prepare)
NEXT: azure-deploy
```

---

### **AI & LLM Skills**

#### 4. **azure-ai**
```
WHEN: "search across data", "vector search", "RAG", "transcribe", "speech-to-text"
INCLUDES: Azure AI Search, Cognitive Services, Speech API, Document Intelligence
OUTPUT: Search index, embeddings, translations
ROUTING: Use for search/speech/OCR. For managing models, use azure-hosted-copilot-sdk or azure-prepare
```

#### 5. **azure-hosted-copilot-sdk** ⭐ COPILOT APPS
```
WHEN: "build copilot app", "create @github/copilot-sdk app", "copilot chat"
WORKFLOW: Scaffold → Integrate SDK → Deploy
OUTPUT: Working copilot-powered application
PREREQUISITE: Node.js/TypeScript project
ROUTING: Specialized for Copilot SDK. Use this FIRST for copilot projects
```

#### 6. **azure-aigateway**
```
WHEN: "API gateway", "gateway policies", "AI governance", "semantic caching"
INCLUDES: APIM as AI gateway, token limit, content safety, rate limiting
ROUTING: For existing APIM resources. azure-prepare handles initial APIM setup
```

---

### **Observability & Diagnostics**

#### 7. **azure-observability**
```
WHEN: "monitoring", "dashboards", "alerts", "Application Insights"
INCLUDES: Log Analytics, Workbooks, Metrics, KQL queries
OUTPUT: Dashboards, alerts, tracing setup
ROUTING: High-level observability. For specific KQL queries, use azure-kusto
```

#### 8. **azure-diagnostics**
```
WHEN: "app broken", "troubleshoot", "debug container app", "fix failures"
INCLUDES: Log analysis, health checks, error diagnosis
OUTPUT: Root cause + fix recommendations
ROUTING: Use when something's wrong after deployment
```

#### 9. **azure-kusto**
```
WHEN: "KQL query", "Kusto database", "data explorer", "log analytics"
INCLUDES: Time-series analysis, anomaly detection, alerting
ROUTING: For specific queries. Use azure-observability for setup
```

---

### **Security & Access Control**

#### 10. **azure-rbac**
```
WHEN: "permissions", "role assignment", "who can access", "grant access"
OUTPUT: Roles assigned, CIDR restrictions, service principal created
PREREQUISITE: Know what resource you're protecting
```

#### 11. **azure-compliance**
```
WHEN: "security audit", "compliance check", "best practices review", "HIPAA/PCI"
OUTPUT: Compliance report, security fixes recommended
ROUTING: For audits. azure-rbac handles actual role assignments
```

#### 12. **entra-app-registration**
```
WHEN: "OAuth setup", "app registration", "MSAL", "Azure AD auth"
OUTPUT: App registration configured, connection strings ready
ROUTING: For authentication setup. Not for RBAC (use azure-rbac)
```

---

### **Infrastructure & Compute**

#### 13. **azure-compute**
```
WHEN: "which VM size?", "VM sizing", "VMSS", "autoscale", "HPC"
OUTPUT: VM recommendations with cost/performance trade-offs
NOTE: Analysis only - use azure-deploy to actually provision
```

#### 14. **azure-prepare** (infrastructure generation)
```
Generates: Bicep/Terraform for compute resources
See "Entry Points" section above
```

---

### **Storage & Data**

#### 15. **azure-storage**
```
WHEN: "blob storage", "file shares", "queue", "table storage", "data lake"
OUTPUT: Storage account configured, access tiers set
ROUTING: Object storage. For time-series data, use azure-kusto
```

#### 16. **azure-kusto** (also listed above)
```
For querying large datasets with KQL
```

---

### **Messaging**

#### 17. **azure-messaging**
```
WHEN: "Event Hubs", "Service Bus", "SDK issue", "message not arriving"
OUTPUT: Queue configured, connection strings, troubleshooting guide
ROUTING: For messaging. Use azure-observability for monitoring queues
```

---

### **Cost Management**

#### 18. **azure-cost-optimization**
```
WHEN: "reduce spending", "cost analysis", "rightsize VMs", "find waste"
OUTPUT: Cost savings report with specific actions
ROUTING: Analysis + recommendations. Use azure-deploy to implement
```

---

### **Migration & Advanced**

#### 19. **azure-cloud-migrate**
```
WHEN: "move from AWS", "GCP to Azure", "Lambda to Functions", "cross-cloud"
OUTPUT: Code converted, architecture mapped to Azure services
ROUTING: For cross-cloud projects. Use azure-prepare after migration analysis
```

#### 20. **azure-resource-lookup**
```
WHEN: "list my resources", "find resource group", "what Am I paying for"
OUTPUT: List of resources with IDs, locations, types
ROUTING: For inventory. Use azure-cost-optimization for analysis
```

#### 21. **azure-resource-visualizer**
```
WHEN: "draw architecture diagram", "show relationships", "Mermaid diagram"
OUTPUT: Visual architecture diagram showing resource connections
ROUTING: Visualization only. Use azure-prepare for actual setup
```

---

## 🔄 Workflow Decision Trees

### Workflow 1: **New Project**

```
User Request: "Build a REST API"
        ↓
┌─────────────────────────────────┐
│ START: azure-prepare             │
│ → Gather requirements            │
│ → Select recipe (azd/bicep/tf)   │
│ → Generate plan.md               │
│ → Create infrastructure code     │
│ → Harden security                │
└──────────────┬────────────────────┘
               ↓
         Is plan good?
         /              \
       YES               NO
        ↓                ↓
┌──────────────┐   Revise &
│ azure-validate   re-run
└──────┬───────┘
       ↓
       Ready to deploy? → NO → Revise plan
       ↓ YES
┌──────────────┐
│ azure-deploy │
│ Run azd up   │
└──────┬───────┘
       ↓
   Deployed! → Problems? → azure-diagnostics
```

### Workflow 2: **Troubleshooting**

```
User Request: "My app stopped working"
        ↓
┌──────────────────────────┐
│ START: azure-diagnostics │
│ → Collect logs           │
│ → Analyze errors         │
│ → Find root cause        │
└──────┬───────────────────┘
       ↓
   Root cause identified?
   /        |        \
Route      Config    Resource
Option    Issue      Issue
  ↓         ↓          ↓
Use    Check RBAC   Check
azure-  with azure- usage with
rbac    rbac      azure-
                   resource-
                   lookup
```

### Workflow 3: **Cost Optimization**

```
User Request: "We're spending too much"
        ↓
┌──────────────────────────────────┐
│ START: azure-cost-optimization   │
│ → Analyze spending               │
│ → Find waste                     │
│ → Generate recommendations       │
└──────┬───────────────────────────┘
       ↓
   Follow recommendations
   /      |      \
VM    Storage   Other
Right-  Tier   Services
size    Change
```

---

## 🛡️ Common Pitfalls & How to Avoid Them

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Skipping validation | Deploy fails → costly rollback | **Always run azure-validate before azure-deploy** |
| Forgetting RBAC | App can't access resources | **Use azure-rbac for permissions, not in code** |
| No plan in .azure/plan.md | Deploy sees no instructions | **azure-prepare MUST run first** |
| Using wrong skill | Takes longer, frustrated user | **Use quick reference above** |
| Compliance surprises | Security audit fails | **Run azure-compliance early, not just before go-live** |
| Wrong VM size chosen | Bad performance or high cost | **Use azure-compute BEFORE provisioning** |
| Don't know what's running | Unexpected charges | **Use azure-resource-lookup + azure-observability** |

---

## 📞 Skill Support Matrix

| Skill | Complexity | Learning Curve | When to Ask Questions |
|-------|-----------|---------------|--------------------|
| azure-prepare | Medium | 1-2 hours | When unsure about architecture |
| azure-deploy | Low | 30 min | When hitting Azure-specific errors |
| azure-validate | Low | 30 min | When validation fails unexpectedly |
| azure-diagnostics | Medium | 1-2 hours | When troubleshooting is hard |
| azure-ai | High | 4-6 hours | When RAG/embeddings not working |
| azure-rbac | Medium | 2-3 hours | When permissions are complex |
| azure-compute | Medium | 2-3 hours | When sizing is critical |
| azure-cost-optimization | Medium | 2-3 hours | When analyzing large bills |
| Others | Low-Medium | <1 hour | Domain-specific questions |

---

## 🎓 Learning Path

**If you're new to Azure:**
1. Read this registry
2. Run `azure-prepare` on a test project
3. Run `azure-validate` to see what it checks
4. Run `azure-deploy` to go live
5. Explore `azure-observability` to understand monitoring
6. Try `azure-diagnostics` if anything breaks

**If you're migrating from another cloud:**
1. Start with `azure-cloud-migrate`
2. Let it analyze your existing code
3. Use output as input to `azure-prepare`
4. Follow standard workflow from there

**If you're optimizing costs:**
1. Run `azure-cost-optimization`
2. Use `azure-compute` for VM decisions
3. Use `azure-storage` for storage tiers
4. Re-run `azure-deploy` with new sizing

---

## 🔗 Cross-Sky References

- All skills follow the same **Plan → Create → Validate → Deploy** pattern
- Most skills depend on `azure-prepare` creating the baseline plan
- All post-deploy monitoring uses `azure-observability` or `azure-diagnostics`
- Cost analysis uses `azure-cost-optimization` + `azure-resource-lookup`

---

*This registry is maintained as the single source of truth for Azure skill selection and usage.*

Last updated: 2026-02-28
