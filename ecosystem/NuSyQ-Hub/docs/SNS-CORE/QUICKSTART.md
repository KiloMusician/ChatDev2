# SNS-Core Quick Start Guide

Get started with SNS-Core in 5 minutes!

---

## Method 1: Use the SNS Converter (Easiest)

### Step 1: Copy model.sns

Open [`model.sns`](model.sns) and copy the entire contents.

### Step 2: Give to Your LLM

Paste the `model.sns` content into any LLM (ChatGPT, Claude, Gemini, etc.).

### Step 3: Convert Your Prompts

Ask the LLM:

```
Convert this prompt to SNS notation:

[Your natural language prompt here]
```

### Step 4: Use the SNS Output

Copy the SNS notation and use it in your AI system!

### Example

**You provide**:
```
Analyze the user query and extract keywords.
Then classify the intent as question, complaint, or request.
Return structured results.
```

**LLM converts to**:
```sns
q → kw_extract → kw
q → classify(["question","complaint","request"]) → intent
→ {kw, intent}
```

**Token savings**: ~50 tokens → ~15 tokens (70% reduction)

---

## Method 2: Learn SNS Manually

### Step 1: Learn Core Patterns (5 minutes)

Read [Core Patterns](core-patterns.md) to understand:
- Flow: `a → b → c`
- Pipeline: `a | b | c`  
- Conditional: `x ? y : z`

### Step 2: Try an Example (2 minutes)

**Natural Language**:
```
Filter the documents to keep only those with score above 0.7,
then sort them by relevance, and return the top 5
```

**Convert to SNS**:
```sns
docs | filter(score > 0.7) | sort(relevance) | top(5)
```

Test it with your LLM—it works!

### Step 3: Convert Your First Prompt (10 minutes)

Take an internal AI-to-AI prompt from your system and convert it:

1. Identify operations (extract, classify, filter, etc.)
2. Connect with arrows (`→`) or pipes (`|`)
3. Use abbreviations (`query` → `q`, `keywords` → `kw`)
4. Remove filler words ("please", "carefully", "then")
5. Test with your LLM

---

## Real-World Example

### Your RAG Orchestrator

**Before (Natural Language)**:
```
You are the orchestrator in a RAG pipeline. Analyze the user's query
to extract keywords and classify the intent into one of these categories:
informational, transactional, or navigational. Then expand the keywords
into search terms and infer the relevant document categories. Finally,
return a structured object containing the search terms, categories,
intent, and keywords.
```

**Token count**: ~150 tokens  
**Cost** (at 10K queries/day): ~$45/day

**After (SNS)**:
```sns
q → kw_extract → kw
q → classify(["info","transactional","nav"]) → intent
(kw + q) → expand_q → terms
intent → infer_cats → cats
→ {terms, cats, intent, kw}
```

**Token count**: ~30 tokens  
**Cost** (at 10K queries/day): ~$9/day  
**Savings**: $36/day = $1,080/month 💰

---

## Testing Your SNS

### Quick Test

Give this to ChatGPT/Claude (no context needed):

```sns
q → kw_extract → kw
q → classify(["positive","negative","neutral"]) → sentiment
→ {kw, sentiment}

q = "I love this product!"
```

**Expected output**:
```json
{
  "kw": ["love", "product"],
  "sentiment": "positive"
}
```

**It works!** 🎉

---

## Common Patterns Cheat Sheet

```sns
# Extract and analyze
text → extract_keywords → keywords

# Classify
text → classify(categories) → category

# Pipeline
data | step1 | step2 | step3

# Conditional
score > 0.7 ? keep : discard

# Filter collection
[items] | filter(condition)

# Multiple operations
input → op1 → result1
input → op2 → result2
→ {result1, result2}

# Combine inputs
(input1 + input2) → process → output

# Check and branch
valid ? process : reject
```

---

## Next Steps

### Immediate (Today)
- [ ] Convert 1 internal AI prompt to SNS
- [ ] Test it with your LLM
- [ ] Measure token savings

### This Week
- [ ] Convert all high-volume internal prompts
- [ ] Calculate monthly cost savings
- [ ] Share results with team

### This Month
- [ ] Consider training an SLM on SNS (see [SLM Training Guide](docs/slm-training.md))
- [ ] Build SNS into your deployment pipeline
- [ ] Contribute your use case back to the community

---

## Get Help

- **Questions**: [GitHub Discussions](https://github.com/EsotericShadow/sns-core/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/EsotericShadow/sns-core/issues)
- **Examples**: See [examples/](examples/) directory
- **Full Docs**: See [README.md](README.md)

---

## Tips for Success

1. **Start small**: Convert one prompt first
2. **Use model.sns**: Let the LLM do the conversion
3. **Verify quality**: Compare outputs to natural language version
4. **Measure savings**: Track token counts
5. **Share learnings**: Contribute back to the community

---

Ready to save 60-85% on your AI costs? **Let's go!** 🚀

---

**Repository**: [github.com/EsotericShadow/sns-core](https://github.com/EsotericShadow/sns-core)
