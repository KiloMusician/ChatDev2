# SNS Philosophy

## The Problem

AI systems talk to each other using natural language prompts designed for humans, not machines.

### Example: Agent Communication

**Current approach** (what we do):
```
You are Agent 2 in a multi-stage RAG pipeline. Agent 1 has analyzed the user's
query and determined that the user is asking about noise complaints. Your job
is to take the search results provided by the retrieval system and rank them
based on relevance to the user's original query. Filter out any results with
a relevance score below 0.7. If fewer than 3 results remain after filtering,
expand the search to include related categories. Return the filtered and ranked
results.
```

**Token count**: ~180 tokens  
**Information density**: Low  
**Cost per call**: $0.001-0.003

**At scale** (1000 queries/day):
- 180,000 tokens/day in agent communication alone
- $1-3/day = $30-90/month
- Just for agents talking to each other!

### The Insight

**LLMs already understand shorthand**. They're trained on:
- Code (with abbreviations like `fn`, `var`, `str`)
- Math notation (`x → y`, `f(x)`, `∑`)
- Academic papers (abbreviations everywhere)
- Programming docs (terse examples)
- Human shorthand (notes, tweets, texts)

We don't need to teach them SNS. We just use what they already know.

---

## The Solution: SNS

**Shorthand Notation Script** - intuitive, token-efficient notation that LLMs naturally parse.

### Same Example in SNS:
```sns
# Agent 2: Discriminator
candidates → rank(q) → scored
scored >> filter(score > 0.7) → relevant

relevant.length < 3 ? expand_search(q, infer_cats(intent)) : relevant
→ results
```

**Token count**: ~35 tokens  
**Information density**: High  
**Savings**: 80%

**At scale** (1000 queries/day):
- 35,000 tokens/day
- $0.20-0.60/day = $6-18/month
- **Savings**: $24-72/month on one agent communication

---

## Core Philosophy

### 1. Notation, Not Language

**SNS is not a programming language**.

It's shorthand notation, like:

**Musical Notation**:
- Musicians don't "execute" sheet music
- They interpret it intuitively
- Different musicians → slightly different performances
- Still fundamentally correct

**Mathematical Notation**:
- `f(x) = x²` is understood universally
- No "compiler" needed
- Humans and machines both get it

**SNS**:
- LLMs don't "compile" SNS
- They interpret it intuitively
- Different LLMs → slightly different internal processing
- Still produces correct results

### 2. Intuitive > Formal

If it feels right, it probably works.

**Examples that just work**:
```sns
# Everyone knows what these mean
text → lowercase → trimmed
items | filter | sort | top(5)  
score > 0.7 ? keep : discard
results +boost(recent)
query ~match docs
```

No formal specification needed. Your intuition is the spec.

### 3. No Training Required

**Traditional programming language**:
```python
# LLM needs to know Python syntax
def analyze(query: str) -> Dict[str, Any]:
    return {"result": process(query)}
```

**SNS**:
```sns
# LLM already understands this
query → analyze → {result}
```

The second one requires **zero explanation**. LLM sees `→` and knows "transform this to that".

### 4. Creative Freedom

SNS embraces creativity. If it's logical, try it!

**Emoji as operators** (why not?):
```sns
query 🎯 find_exact_match
results ⚡ boost(recent)  
docs 🔍 deep_search
candidates ⚖️ rank_by_weight
urgent 🚨 flag_priority
text ✂️ trim_excess
```

**Do LLMs understand emoji?** YES! They're trained on billions of social media posts.

**Custom abbreviations**:
```sns
q = query
kw = keywords
cats = categories
docs = documents
rel = relevance
sim = similarity
```

LLMs figure it out from context.

### 5. Consistency Helps (But Isn't Required)

**Recommended pattern** (consistency):
```sns
# Use → for transformations
input → operation → output

# Use | for pipelines
data | step1 | step2 | step3

# Use +/- for modifiers
results +boost -penalty
```

**But variations work too**:
```sns
# These all work
input → process → output
input >> process >> output
input |> process |> output
process(input) → output
```

LLMs are flexible. Use what feels natural.

---

## Design Principles

### Principle 1: Token Efficiency First

Every token costs money. Every token adds latency.

**Question to ask**: "Is this word necessary?"

❌ Verbose:
```
Please carefully extract the keywords from the text
```

✅ Concise:
```
text → kw_extract
```

✅ Even shorter:
```
txt→kw
```

**But**: Don't sacrifice clarity for 1-2 tokens. Balance efficiency and readability.

### Principle 2: Leverage Existing Knowledge

Use conventions LLMs already know:

**From programming**:
- `fn`, `var`, `str`, `int`, `bool`
- `if/else`, `while`, `for`
- `filter`, `map`, `reduce`, `sort`

**From math**:
- `→` (maps to)
- `∑` (sum)
- `∈` (element of)
- `~` (approximately)

**From general use**:
- `+` (add, boost, positive)
- `-` (remove, penalty, negative)
- `*` (emphasize, multiply)
- `?` (question, conditional, optional)
- `!` (important, not, negate)

### Principle 3: Readable by Humans

SNS should be understandable to developers, not just LLMs.

**Good balance**:
```sns
q → kw_extract → kw
q → classify(intent_types) → intent
kw + q → expand_q → terms
→ {kw, intent, terms}
```

A human can read this and understand: "Extract keywords, classify intent, expand query, return object".

**Too cryptic** (don't do this):
```sns
q→k→i→e→o
```

This saves 5 tokens but loses all readability.

### Principle 4: Context Matters

SNS can be more aggressive in shortening when context is clear.

**First use** (establish meaning):
```sns
query → keyword_extract → keywords
```

**Subsequent uses** (context established):
```sns
keywords → expand → terms
terms → search → results
```

**In tight context** (very clear):
```sns
q→kw→expand→search→results
```

### Principle 5: Fail Gracefully

If LLM doesn't understand notation, it'll ask or make reasonable guess.

**Ambiguous notation**:
```sns
x ¿¿ y  # Unclear symbol
```

**LLM behavior**: Likely asks for clarification or infers from context.

**Better**:
```sns
x → y  # Clear transformation
```

---

## Why This Works: The Science

### LLMs Are Pattern Matchers

LLMs don't "understand" in human sense. They:
1. See patterns in training data
2. Match new input to learned patterns
3. Generate likely continuations

**Training data includes**:
- Billions of lines of code (shorthand everywhere)
- Math papers (notation heavy)
- Technical docs (abbreviations)
- Social media (informal shorthand)

**Result**: LLMs are **excellent** at parsing shorthand.

### Example: How LLM Processes SNS

**You write**:
```sns
query → kw_extract → kw
```

**LLM's internal process** (simplified):
1. Sees `→` - knows this means "transform" or "map"
2. Sees `query` - understands this is input
3. Sees `kw_extract` - recognizes keyword extraction pattern
4. Sees `→ kw` - understands result stored as `kw`
5. Generates: Extract keywords from query and store them

**No explicit instruction needed**. Pattern matching does it all.

### Evidence It Works

We tested SNS with multiple LLMs:
- GPT-4, Claude, Llama, Mistral
- Different notations
- Complex multi-step operations

**Result**: 95%+ accuracy in interpretation
- Same output as natural language prompts
- Significantly fewer tokens
- No degradation in quality

See [Proof It Works](examples/proof-it-works.md) for details.

---

## Common Questions

### "Isn't this just pseudo-code?"

**Similar but different**:

**Pseudo-code**: Meant for humans to read, later converted to real code
**SNS**: Meant for LLMs to execute directly, never becomes code

**Pseudo-code**:
```
FOR each document IN documents:
    IF document.score > threshold:
        ADD document TO filtered_results
```

**SNS**:
```sns
docs >> filter(score > threshold) → filtered
```

SNS is much more compact and LLM-optimized.

### "What if LLM doesn't understand?"

**Rare**, but when it happens:
1. LLM asks for clarification
2. LLM makes reasonable guess
3. You refine notation

**Example**:
```sns
# Unclear
x ⇝⇝ y

# LLM might ask: "What does ⇝⇝ mean?"
# You clarify: "double transformation"
# Or just use: x → intermediate → y
```

**Best practice**: Stick to well-established symbols first.

### "Can I mix SNS and natural language?"

**Absolutely!**

```sns
# Analyze the user's query for keyword extraction
query → kw_extract → keywords

# Now classify the intent
query → classify(["info", "complaint", "procedure"]) → intent

# Combine results
→ {keywords, intent}
```

Comments in natural language, operations in SNS. Best of both worlds.

### "Is there a formal specification?"

**No, and that's intentional**.

Formal specs lead to:
- Rigid syntax
- Parsing errors
- Need for documentation
- Training overhead

SNS is **intentionally informal**. If it works, it's valid SNS.

### "What about edge cases?"

**Embrace ambiguity**:
```sns
# Could mean multiple things
x ~ y
```

Could be:
- x is similar to y
- Fuzzy match x against y
- Approximate x with y

**Solution**: Context makes it clear. LLMs use context to disambiguate (just like humans).

---

## Real-World Impact

### Case Study: 3-Stage RAG Pipeline

**Before SNS**:
- Orchestrator prompt: 200 tokens
- Discriminator prompt: 180 tokens
- Responder prompt: 150 tokens (kept natural language - user facing)
- **Total internal**: 380 tokens

**After SNS**:
- Orchestrator prompt: 45 tokens
- Discriminator prompt: 40 tokens  
- Responder prompt: 150 tokens (unchanged)
- **Total internal**: 85 tokens

**Savings**: 295 tokens per query (77% reduction on internal comms)

**At 1000 queries/day**:
- 295,000 tokens saved per day
- 8,850,000 tokens saved per month
- ~$90-180 saved per month (depending on model)

**At 10,000 queries/day** (medium scale):
- $900-1,800 saved per month
- $10,800-21,600 saved per year

### Case Study: Multi-Agent System

**Scenario**: 5 agents, each communicates with 2 others, 100 messages/agent/day

**Before SNS**: 500 messages × 150 tokens = 75,000 tokens/day

**After SNS**: 500 messages × 35 tokens = 17,500 tokens/day

**Savings**: 57,500 tokens/day = 1,725,000 tokens/month = ~$175/month

---

## Philosophy Summary

SNS is built on beliefs:

1. **AI efficiency matters** - Tokens = money and latency
2. **Intuition > formality** - What feels right usually works
3. **LLMs are smart** - They understand shorthand naturally
4. **Notation > language** - No grammar, no rules, just patterns
5. **Practical > perfect** - Use what works, iterate what doesn't
6. **Open > proprietary** - Anyone can use and extend SNS

---

## Getting Started

Ready to use SNS?

1. **[Core Patterns](core-patterns.md)** - Learn the basic patterns (5 min)
2. **[Examples](examples/orchestrator.md)** - See real implementations (10 min)
3. **Start using** - Try it in your next prompt (immediate)

No setup. No installation. No training. **Just write and it works.**

---

## Contributing

SNS grows through community use. Share:
- Patterns that work well
- Creative notations
- Token savings data
- Use cases and examples

**SNS is notation, not software**. There's no "official implementation". Your usage is valid if it works for you.

---

Want to dive deeper? Continue to [Core Patterns](core-patterns.md).
