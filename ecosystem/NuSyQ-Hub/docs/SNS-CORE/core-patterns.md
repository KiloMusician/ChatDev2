# Core Patterns

SNS uses intuitive patterns that LLMs naturally understand. No formal grammar, just conventions that feel right.

---

## Pattern 1: Flow / Transform

**Notation**: `input → operation → output`

The arrow (`→`) means "transform to" or "flows into".

### Examples

```sns
query → analyze → insights
```
**Meaning**: Transform query into insights via analysis

```sns
text → normalize → lower → trim → clean_text
```
**Meaning**: Flow text through normalization, lowercasing, and trimming

```sns
doc → extract_keywords → kw
```
**Meaning**: Extract keywords from document

### Token Comparison

| Natural Language | SNS | Savings |
|-----------------|-----|---------|
| "Extract keywords from the document" (6 tokens) | `doc → kw_extract` (4 tokens) | 33% |
| "Normalize and clean the text" (6 tokens) | `text → normalize → clean` (5 tokens) | 17% |
| "Transform the query into search terms" (7 tokens) | `query → search_terms` (4 tokens) | 43% |

### Why It Works

`→` is universal:
- Math: `f: X → Y` (function maps X to Y)
- Code: `=>` in JavaScript (arrow functions)
- Diagrams: Flowcharts use arrows
- Natural: "goes to", "becomes", "transforms into"

LLMs have seen millions of arrows in training data. They get it instantly.

---

## Pattern 2: Pipeline

**Notation**: `data | step1 | step2 | step3`

The pipe (`|`) means "pass through" or "then".

### Examples

```sns
docs | filter | score | sort | top(5)
```
**Meaning**: Filter docs, score them, sort by score, take top 5

```sns
text | lower | trim | tokenize | remove_stopwords
```
**Meaning**: Pipeline of text processing steps

```sns
candidates | rank(query) | threshold(0.7) | dedupe
```
**Meaning**: Rank candidates, filter by threshold, remove duplicates

### Token Comparison

| Natural Language | SNS | Savings |
|-----------------|-----|---------|
| "Filter the documents, score them, sort by score, and take the top 5" (15 tokens) | `docs \| filter \| score \| sort \| top(5)` (10 tokens) | 33% |
| "Process the text by lowercasing, trimming, and tokenizing" (10 tokens) | `text \| lower \| trim \| tokenize` (7 tokens) | 30% |

### Why It Works

Pipes are everywhere:
- Unix: `cat file | grep pattern | sort`
- Programming: Method chaining, pipelines
- Data: ETL pipelines

LLMs recognize this pattern immediately.

---

## Pattern 3: Conditional / Ternary

**Notation**: `condition ? true_action : false_action`

Classic ternary operator. Everyone knows it.

### Examples

```sns
score > 0.7 ? keep : discard
```
**Meaning**: If score above 0.7, keep; otherwise discard

```sns
results.length < 3 ? expand_search() : return_results
```
**Meaning**: If fewer than 3 results, expand search; else return

```sns
intent == "complaint" ? escalate : normal_process
```
**Meaning**: Route based on intent type

```sns
text ? process(text) : null
```
**Meaning**: Process if text exists, else null

### Token Comparison

| Natural Language | SNS | Savings |
|-----------------|-----|---------|
| "If the score is greater than 0.7, keep the item; otherwise, discard it" (15 tokens) | `score > 0.7 ? keep : discard` (8 tokens) | 47% |
| "If there are fewer than 3 results, expand the search; otherwise return results" (15 tokens) | `results.length < 3 ? expand_search() : return_results` (10 tokens) | 33% |

### Why It Works

Ternary operator is in:
- JavaScript: `x ? y : z`
- Python: `y if x else z`
- C/Java: `x ? y : z`
- Math: Piecewise functions

Universal pattern.

---

## Pattern 4: Collection Operations

**Notation**: `[collection] >> operation` or `operation([collection])`

Apply operations to lists, maps, sets.

### Examples

```sns
[items] >> filter(score > 0.7)
```
**Meaning**: Filter items by score

```sns
[docs] >> map(extract_title) >> sort
```
**Meaning**: Extract titles from docs and sort

```sns
{map} ++ {new_data}
```
**Meaning**: Merge two maps

```sns
[a, b, c] & [b, c, d] → [b, c]
```
**Meaning**: Intersection of two sets

### Token Comparison

| Natural Language | SNS | Savings |
|-----------------|-----|---------|
| "Filter the items to only include those with score greater than 0.7" (14 tokens) | `[items] >> filter(score > 0.7)` (8 tokens) | 43% |
| "Map over the documents and extract the title from each" (12 tokens) | `[docs] >> map(extract_title)` (6 tokens) | 50% |

### Why It Works

Collection operations are fundamental:
- Functional programming: `map`, `filter`, `reduce`
- SQL: `WHERE`, `SELECT`, `GROUP BY`
- Array methods everywhere

LLMs have seen these thousands of times.

---

## Pattern 5: Modifiers

**Notation**: `+boost`, `-penalty`, `*emphasize`, `~fuzzy`

Symbols modify behavior or values.

### Examples

```sns
results +boost(recency) +boost(location)
```
**Meaning**: Apply recency and location boosts to results

```sns
score *2
```
**Meaning**: Double the score (emphasize)

```sns
query ~match docs
```
**Meaning**: Fuzzy match query against docs

```sns
items -remove(duplicates)
```
**Meaning**: Remove duplicates from items

### Token Comparison

| Natural Language | SNS | Savings |
|-----------------|-----|---------|
| "Apply a recency boost and location boost to the results" (11 tokens) | `results +boost(recency) +boost(location)` (6 tokens) | 45% |
| "Perform a fuzzy match of the query against the documents" (11 tokens) | `query ~match docs` (4 tokens) | 64% |

### Why It Works

Math operators are intuitive:
- `+` always means "add" or "enhance"
- `-` always means "subtract" or "reduce"
- `*` means "multiply" or "emphasize"
- `~` means "approximately" or "fuzzy"

No explanation needed.

---

## Pattern 6: Abbreviations

**Notation**: Use common abbreviations LLMs recognize

### Common Abbreviations

```sns
q = query
kw = keywords
doc/docs = document(s)
txt = text
cat/cats = category/categories
rel = relevance
sim = similarity
norm = normalize
ext = extract
cls = classify
filt = filter
param/params = parameter(s)
res = result(s)
temp = temporary/template
prev = previous
curr = current
```

### Examples

```sns
q → kw_ext → kw
```
Instead of:
```sns
query → keyword_extract → keywords
```

```sns
docs | filt | cls(cats) → res
```
Instead of:
```sns
documents | filter | classify(categories) → results
```

### Token Comparison

| Full Form | Abbreviated | Savings |
|-----------|-------------|---------|
| `query → keyword_extract → keywords` (5 tokens) | `q → kw_ext → kw` (5 tokens) | 0%* |
| `documents \| filter \| classify(categories) → results` (7 tokens) | `docs \| filt \| cls(cats) → res` (7 tokens) | 0%* |

**Note**: Savings come from shorter tokens. `query` might be 1-2 tokens, `q` is always 1 token.

### Why It Works

Abbreviations are everywhere:
- Variable names in code (`i`, `j`, `k`, `x`, `y`)
- Technical docs (`param`, `arg`, `temp`)
- Common English (`doc`, `info`, `app`)

LLMs trained on billions of abbreviated text.

---

## Pattern 7: Object Construction

**Notation**: `{key: value, key2: value2}` or `{key, key2, key3}`

Build structured outputs.

### Examples

```sns
→ {keywords, intent, search_terms}
```
**Meaning**: Return object with these fields

```sns
result = {
  query: q,
  results: docs,
  count: docs.length,
  timestamp: now()
}
```
**Meaning**: Structured result object

```sns
{...existing, new_field: value}
```
**Meaning**: Spread existing object, add new field

### Token Comparison

| Natural Language | SNS | Savings |
|-----------------|-----|---------|
| "Return an object containing keywords, intent, and search_terms" (9 tokens) | `→ {keywords, intent, search_terms}` (6 tokens) | 33% |
| "Create a result object with query, results, count, and timestamp fields" (13 tokens) | `{query, results, count, timestamp}` (7 tokens) | 46% |

### Why It Works

Object notation is universal:
- JavaScript: `{key: value}`
- JSON: Same syntax
- Python: Dictionary syntax similar
- Every API response format

---

## Pattern 8: Function Calls

**Notation**: `function_name(args)` or `fn(args)`

Simple function call syntax.

### Examples

```sns
classify(text, categories)
```
**Meaning**: Classify text into categories

```sns
search(query, docs, {limit: 10})
```
**Meaning**: Search docs with limit parameter

```sns
filter(items, fn(x) -> x.score > 0.7)
```
**Meaning**: Filter with inline function

### Token Comparison

| Natural Language | SNS | Savings |
|-----------------|-----|---------|
| "Classify the text into the given categories" (8 tokens) | `classify(text, categories)` (5 tokens) | 38% |
| "Search the documents using the query with a limit of 10" (13 tokens) | `search(query, docs, {limit: 10})` (8 tokens) | 38% |

### Why It Works

Function calls are fundamental to programming. Every LLM has seen millions of them.

---

## Pattern 9: Assignment

**Notation**: `variable = value` or `variable: type = value`

Simple assignment.

### Examples

```sns
keywords = extract_keywords(query)
```

```sns
score: float = calculate_score(doc, query)
```

```sns
results = search(query) | filter | sort
```

### Why It Works

Assignment is universal across all programming languages.

---

## Pattern 10: Loops (Implied)

**Notation**: `for item in items:` or `items.each(fn)`

Loops when needed (use sparingly - often implied).

### Examples

```sns
for doc in docs:
  doc.score = calculate_score(doc, query)
```

Or more SNS-style:
```sns
docs >> map(doc → {doc, score: calc_score(doc, q)})
```

### Token Comparison

| Explicit Loop | SNS Pipeline | Savings |
|---------------|--------------|---------|
| `for doc in docs: score(doc)` (8 tokens) | `docs >> score` (3 tokens) | 63% |

### Why It Works

Loops are implied by operations on collections. Usually better to use `map`, `filter`, etc.

---

## Combining Patterns

Real power comes from combining patterns:

### Example: Full RAG Orchestrator

```sns
# Extract and analyze
q → kw_extract → kw
q → classify(["info","complaint","procedure"]) → intent

# Expand query
(kw + q) → expand_q → search_terms

# Infer categories
intent → infer_cats → cats

# Boost if needed
cats.includes("urgent") ? search_terms +boost(priority) : search_terms

# Return structured
→ {
  search_terms,
  categories: cats,
  intent,
  keywords: kw
}
```

**Token count**: ~55 tokens

**Natural language equivalent**: ~200 tokens

**Savings**: 72%

---

## Pattern Summary

| Pattern | Notation | Use Case |
|---------|----------|----------|
| Flow | `a → b → c` | Transformations |
| Pipeline | `a \| b \| c` | Sequential operations |
| Conditional | `x ? y : z` | Branching logic |
| Collection | `[items] >> op` | List/map/set operations |
| Modifier | `+boost -penalty` | Modify values/behavior |
| Abbreviation | `q, kw, doc` | Shorten common terms |
| Object | `{key: val}` | Structured output |
| Function | `fn(args)` | Call operations |
| Assignment | `x = y` | Store results |
| Loop | `for x in xs` | Iteration (use sparingly) |

---

## Best Practices

### 1. Start with Clarity

When first using SNS, prefer clarity over brevity:

```sns
# Clear
query → keyword_extract → keywords

# Very short (use after established)
q→kw_ext→kw
```

### 2. Use Context

Once variables are established, abbreviate heavily:

```sns
# Establish
query → analyze → analysis

# Now can use
query → ...
q → ...  # Context makes this clear
```

### 3. Mix Patterns

```sns
# Flow + conditional + object
q → analyze → analysis
analysis.confidence > 0.8 ? analysis : fallback_analysis(q)
→ {query: q, analysis, confidence}
```

### 4. Comment When Helpful

```sns
# Extract semantic concepts
q → kw_extract → kw

# Classify user intent  
q → classify(intent_types) → intent
```

### 5. Stay Consistent Within a Prompt

Pick a style and stick to it:

```sns
# Good - consistent
q → kw_extract → kw
q → classify(types) → intent
kw + q → expand → terms

# Bad - inconsistent
q → kw_extract → kw
classify(q, types) → intent
terms = expand(kw + q)
```

---

## Anti-Patterns (What to Avoid)

### 1. Over-Abbreviation

❌ Too cryptic:
```sns
q→k→e→t→s
```

✅ Readable:
```sns
q → kw_extract → expand → terms → search
```

### 2. Unclear Symbols

❌ Inventing symbols:
```sns
x ¿¿ y  # What does ¿¿ mean?
```

✅ Standard symbols:
```sns
x → y  # Clear transformation
```

### 3. Overcomplicating

❌ Too complex:
```sns
((((a | b) >> c) → d) + e) | f
```

✅ Break it down:
```sns
step1 = (a | b) >> c
step2 = step1 → d
step3 = step2 + e
result = step3 | f
```

### 4. Ignoring Context

❌ No context:
```sns
x → y → z
```

✅ With context:
```sns
# Analyze query
query → extract_keywords → expand → search_terms
```

---

## Next Steps

Now that you know the core patterns:

1. **[Operations Guide](operations/text-ops.md)** - See patterns applied to specific operations
2. **[Examples](examples/orchestrator.md)** - Real-world SNS code
3. **[Symbols Reference](symbols.md)** - Complete symbol guide

Ready to see real applications? Check out the [Operations Guide](operations/text-ops.md)!
