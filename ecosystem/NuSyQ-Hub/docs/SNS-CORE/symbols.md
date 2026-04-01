# Symbols Reference

Complete guide to all symbols used in SNS notation.

---

## Flow & Transform Symbols

### → (Right Arrow)

**Meaning**: Transform, flow, maps to

**Usage**:
```sns
input → operation → output
query → analyze → result
text → normalize → clean
```

**Why it works**: Universal in math (f: X → Y), code (=>), diagrams  
**Token savings**: ~60-80% vs "transform into"

---

### ← (Left Arrow)

**Meaning**: Reverse flow, assign from (rarely used)

**Usage**:
```sns
result ← process(data)  # Alternative to =
```

**Note**: Less common, prefer `=` or `→`

---

### ⇒ (Double Arrow)

**Meaning**: Strong implication, guaranteed transform

**Usage**:
```sns
valid_input ⇒ success
invalid_input ⇒ error
```

**Token savings**: ~70% vs "will definitely result in"

---

## Pipeline Symbols

### | (Pipe)

**Meaning**: Pass through, then, pipeline

**Usage**:
```sns
data | step1 | step2 | step3
items | filter | sort | take(5)
```

**Why it works**: Unix pipes, method chaining  
**Token savings**: ~70% vs "and then"

---

### >> (Right Shift / Forward)

**Meaning**: Apply operation, pass forward

**Usage**:
```sns
[items] >> map(fn)
data >> process >> output
```

**Token savings**: ~65% vs "apply the operation"

---

### << (Left Shift / Backward)

**Meaning**: Reverse operation, pull from

**Usage**:
```sns
result << source
data << fetch(api)
```

**Note**: Less common, prefer →

---

## Comparison Symbols

### == (Equal)

**Meaning**: Equality check

**Usage**:
```sns
value == target
intent == "complaint"
```

**Token savings**: ~60% vs "is equal to"

---

### != (Not Equal)

**Meaning**: Inequality check

**Usage**:
```sns
value != null
status != "complete"
```

**Token savings**: ~65% vs "is not equal to"

---

### ≠ (Not Equal Symbol)

**Meaning**: Same as !=

**Usage**:
```sns
value ≠ target
```

**Token savings**: ~65% vs "is not equal to"

---

### > < >= <= (Comparisons)

**Meaning**: Greater, less, greater-or-equal, less-or-equal

**Usage**:
```sns
score > 0.7
count < 10
value >= threshold
age <= 18
```

**Token savings**: ~70% vs "greater than", etc.

---

### ≤ ≥ (Comparison Symbols)

**Meaning**: Less-than-or-equal, greater-than-or-equal

**Usage**:
```sns
value ≤ max
score ≥ min
```

**Token savings**: ~70% vs written form

---

## Logical Symbols

### && (Logical AND)

**Meaning**: Both conditions must be true

**Usage**:
```sns
score > 0.7 && category == "bylaw"
valid && active
```

**Token savings**: ~60% vs "and"

---

### || (Logical OR)

**Meaning**: Either condition can be true

**Usage**:
```sns
status == "pending" || status == "active"
error || warning
```

**Token savings**: ~60% vs "or"

---

### ! (NOT)

**Meaning**: Negate, logical not

**Usage**:
```sns
!valid
!found
!isEmpty(list)
```

**Token savings**: ~70% vs "not"

---

### ¬ (NOT Symbol)

**Meaning**: Same as !

**Usage**:
```sns
¬condition
```

**Token savings**: ~70% vs "not"

---

### ⊕ (XOR)

**Meaning**: Exclusive or

**Usage**:
```sns
a ⊕ b
```

**Token savings**: ~75% vs "exactly one but not both"

---

## Conditional Symbols

### ? : (Ternary)

**Meaning**: Conditional expression

**Usage**:
```sns
condition ? if_true : if_false
score > 0.7 ? "pass" : "fail"
```

**Token savings**: ~70% vs "if...then...else"

---

### ?? (Null Coalescing)

**Meaning**: Use value if not null, else default

**Usage**:
```sns
value ?? default
result ?? fallback
```

**Token savings**: ~75% vs "use value or default if null"

---

### ?. (Optional Chaining)

**Meaning**: Access property if exists

**Usage**:
```sns
user?.name
data?.results?.items
```

**Token savings**: ~70% vs "if exists then access"

---

## Set & Collection Symbols

### ∈ (Element Of)

**Meaning**: Item is in collection

**Usage**:
```sns
item ∈ collection
"noise" ∈ categories
x ∈ [1, 2, 3]
```

**Token savings**: ~70% vs "is in" or "is contained in"

---

### ∋ (Contains)

**Meaning**: Collection contains item

**Usage**:
```sns
collection ∋ item
categories ∋ "noise"
```

**Token savings**: ~70% vs "contains"

---

### ∉ (Not Element Of)

**Meaning**: Item is not in collection

**Usage**:
```sns
item ∉ collection
"spam" ∉ allowed_types
```

**Token savings**: ~75% vs "is not in"

---

### ∪ (Union)

**Meaning**: Combine sets

**Usage**:
```sns
set1 ∪ set2
tags1 ∪ tags2
```

**Token savings**: ~70% vs "union of"

---

### ∩ (Intersection)

**Meaning**: Common elements

**Usage**:
```sns
set1 ∩ set2
common = tags1 ∩ tags2
```

**Token savings**: ~70% vs "intersection of"

---

### ⊂ (Subset)

**Meaning**: Is subset of

**Usage**:
```sns
subset ⊂ superset
selected ⊂ all_items
```

**Token savings**: ~70% vs "is a subset of"

---

### ⊃ (Superset)

**Meaning**: Is superset of

**Usage**:
```sns
superset ⊃ subset
all_items ⊃ selected
```

**Token savings**: ~70% vs "is a superset of"

---

## Arithmetic & Modifier Symbols

### + (Plus / Add / Boost)

**Meaning**: Add, combine, boost

**Usage**:
```sns
a + b
results +boost(recency)
keywords + context
```

**Token savings**: ~65% vs "add" or "apply boost"

---

### - (Minus / Remove / Penalty)

**Meaning**: Subtract, remove, penalty

**Usage**:
```sns
a - b
results -penalty(old)
items - duplicates
```

**Token savings**: ~65% vs "remove" or "apply penalty"

---

### * (Multiply / Emphasize)

**Meaning**: Multiply, emphasize, amplify

**Usage**:
```sns
score * 2
results *importance
value * factor
```

**Token savings**: ~65% vs "multiply by" or "emphasize"

---

### / (Divide)

**Meaning**: Division

**Usage**:
```sns
total / count
sum / items.length
```

**Token savings**: ~60% vs "divided by"

---

### % (Modulo / Percentage)

**Meaning**: Remainder or percentage

**Usage**:
```sns
x % 2  # modulo
score * 100%  # percentage
```

**Token savings**: ~60% vs "modulo" or "percent"

---

### ^ (Power / Parent / Up)

**Meaning**: Exponent, parent level, up hierarchy

**Usage**:
```sns
x^2  # squared
value^power
category^parent  # parent category
```

**Token savings**: ~65% vs "to the power of"

---

### ++ (Increment / Concatenate)

**Meaning**: Increment or merge

**Usage**:
```sns
count++
list1 ++ list2  # concatenate
{map1} ++ {map2}  # merge
```

**Token savings**: ~70% vs "concatenate" or "merge"

---

### -- (Decrement / Difference)

**Meaning**: Decrement or set difference

**Usage**:
```sns
count--
set1 -- set2  # difference
```

**Token savings**: ~70% vs "set difference"

---

### ** (Emphasize / Power)

**Meaning**: Strong emphasis or power

**Usage**:
```sns
**important**
value ** power
```

**Token savings**: ~65% vs "emphasize strongly"

---

## Similarity & Approximation

### ~ (Approximately / Fuzzy / Similar)

**Meaning**: Approximate, fuzzy match, similarity

**Usage**:
```sns
value ~ target  # approximately
query ~match docs  # fuzzy match
text1 ~sim text2  # similarity
```

**Token savings**: ~75% vs "approximately" or "fuzzy match"

---

### ≈ (Approximately Equal)

**Meaning**: Approximately equal

**Usage**:
```sns
value ≈ target
score ≈ 0.7
```

**Token savings**: ~75% vs "approximately equal to"

---

## Special Operation Symbols

### @ (At / Context / Location)

**Meaning**: At location, in context, reference

**Usage**:
```sns
process @server
evaluate @time(now)
data @context(user)
```

**Token savings**: ~65% vs "at" or "in context of"

---

### # (Count / Number / Comment)

**Meaning**: Count, number, or comment

**Usage**:
```sns
#items  # count of items
#[1, 2, 3]  # returns 3
# This is a comment
```

**Token savings**: ~70% vs "count of" or "number of"

---

### $ (Value / Cost / Variable)

**Meaning**: Value, cost, variable reference

**Usage**:
```sns
$price
$cost_per_item
total * $rate
```

**Token savings**: ~60% vs "value of"

---

### & (AND / Intersection)

**Meaning**: Logical AND or set intersection

**Usage**:
```sns
valid & active
set1 & set2  # intersection
condition1 & condition2
```

**Token savings**: ~65% vs "and" or "intersection"

---

### \ (Difference / Escape)

**Meaning**: Set difference or escape character

**Usage**:
```sns
set1 \ set2  # set difference
text\ncontains\nnewlines  # escape
```

**Token savings**: ~70% vs "set difference"

---

### : (Type / Assign / Case)

**Meaning**: Type annotation, assign, case separator

**Usage**:
```sns
value: type
key: value
case: action
```

**Token savings**: ~60% vs various uses

---

### :: (Scope / Path)

**Meaning**: Scope resolution, path separator

**Usage**:
```sns
module::function
namespace::class
category::subcategory
```

**Token savings**: ~65% vs "in" or "of"

---

### ... (Spread / Rest / Continue)

**Meaning**: Spread operator, rest parameters, continuation

**Usage**:
```sns
{...existing, new: value}  # spread
function(...args)  # rest
```

**Token savings**: ~70% vs "all properties of"

---

### . (Property Access)

**Meaning**: Access property or method

**Usage**:
```sns
object.property
user.name
items.length
```

**Token savings**: ~60% vs "property of"

---

## Emoji Symbols (Creative)

### 🎯 (Target)

**Meaning**: Precise, exact, targeted

**Usage**:
```sns
query 🎯 exact_match
search 🎯 pinpoint
```

**Token savings**: ~80% vs "target precisely"

---

### 🔍 (Search)

**Meaning**: Search, look for

**Usage**:
```sns
query 🔍 docs
text 🔍 find_pattern
```

**Token savings**: ~85% vs "search through"

---

### 🔎 (Magnify)

**Meaning**: Examine closely, detailed search

**Usage**:
```sns
data 🔎 examine
text 🔎 deep_analysis
```

**Token savings**: ~80% vs "examine closely"

---

### 🚨 (Alert / Urgent)

**Meaning**: Urgent, alert, escalate

**Usage**:
```sns
complaint 🚨 escalate
item 🚨 urgent
```

**Token savings**: ~80% vs "mark as urgent"

---

### ⚡ (Boost / Fast)

**Meaning**: Boost, accelerate, enhance

**Usage**:
```sns
results ⚡ boost(recency)
process ⚡ fast_track
```

**Token savings**: ~80% vs "apply boost"

---

### ⚖️ (Balance / Weigh)

**Meaning**: Balance, weigh, rank

**Usage**:
```sns
candidates ⚖️ rank
factors ⚖️ balance
```

**Token savings**: ~80% vs "weigh and rank"

---

### ✂️ (Cut / Trim)

**Meaning**: Trim, cut, filter

**Usage**:
```sns
results ✂️ trim
text ✂️ cut_excess
```

**Token savings**: ~80% vs "trim excess"

---

### ✨ (Clean / Polish)

**Meaning**: Clean, polish, beautify

**Usage**:
```sns
data ✨ clean
text ✨ polish
```

**Token savings**: ~80% vs "clean and polish"

---

### 📦 (Package)

**Meaning**: Package, bundle, wrap

**Usage**:
```sns
results 📦 bundle
data 📦 package
```

**Token savings**: ~80% vs "package together"

---

### ✅ (Check / Verify)

**Meaning**: Verify, approve, correct

**Usage**:
```sns
item ✅ verified
data ✅ approved
```

**Token savings**: ~80% vs "mark as verified"

---

### ❌ (Reject / Invalid)

**Meaning**: Reject, invalid, wrong

**Usage**:
```sns
item ❌ rejected
data ❌ invalid
```

**Token savings**: ~80% vs "mark as rejected"

---

### 🔄 (Cycle / Loop)

**Meaning**: Loop, cycle, repeat

**Usage**:
```sns
process 🔄 until(done)
data 🔄 cycle
```

**Token savings**: ~80% vs "loop until"

---

### 🔥 (Hot / Trending)

**Meaning**: Hot, trending, popular

**Usage**:
```sns
topics 🔥 trending
content 🔥 hot
```

**Token savings**: ~80% vs "mark as trending"

---

### 🚀 (Launch / Accelerate)

**Meaning**: Launch, boost maximum, accelerate

**Usage**:
```sns
process 🚀 launch
item 🚀 prioritize_max
```

**Token savings**: ~80% vs "launch with maximum priority"

---

## Combination Patterns

### Common Combinations

```sns
# Flow with conditional
data → process ? success : error

# Pipeline with filter
items | filter | sort | top(10)

# Boost with modifiers
results +boost(recency) -penalty(old)

# Set operations
set1 ∪ set2 ∩ set3

# Fuzzy search with ranking
query ~search docs | rank ⚖️ | top(5)

# Emoji combination
query 🔍 docs ⚖️ rank ⚡ boost 📦 package
```

---

## Symbol Priority Guide

### High Priority (Use Often)

- `→` Flow/transform
- `|` Pipeline
- `?:` Conditional
- `==`, `!=`, `>`, `<` Comparisons
- `&&`, `||`, `!` Logic
- `+`, `-` Modifiers

### Medium Priority (Use When Clear)

- `~` Fuzzy/similarity
- `∈` Element of
- `++`, `--` Merge/difference
- `??` Null coalescing
- `@` Context
- `#` Count

### Creative (Use Internally)

- Emoji (🎯🔍⚡⚖️✂️✨📦✅❌)
- Mathematical symbols (∪∩⊂⊃)
- Advanced operators (⊕⇒¬)

---

## Quick Reference Table

| Symbol | Name | Usage | Savings |
|--------|------|-------|---------|
| → | Arrow | Transform | 70% |
| \| | Pipe | Pipeline | 70% |
| ? : | Ternary | Conditional | 70% |
| == | Equal | Compare | 65% |
| && | AND | Logic | 60% |
| \|\| | OR | Logic | 60% |
| ! | NOT | Negate | 70% |
| ~ | Tilde | Fuzzy | 75% |
| ∈ | Element | Contains | 70% |
| + | Plus | Add/boost | 65% |
| - | Minus | Remove | 65% |
| * | Multiply | Emphasize | 65% |
| ?? | Null-coal | Default | 75% |
| 🎯 | Target | Precise | 80% |
| 🔍 | Search | Find | 85% |
| ⚡ | Lightning | Boost | 80% |
| ⚖️ | Scale | Balance | 80% |
| ✂️ | Scissors | Trim | 80% |

---

## Best Practices

1. **Start with common symbols**: →, |, ?, ==
2. **Add logical operators**: &&, ||, !
3. **Use modifiers**: +, -, *
4. **Try emoji for fun**: 🎯🔍⚡ (internal only)
5. **Test understanding**: Verify LLM interprets correctly
6. **Be consistent**: Pick your favorites and stick to them

---

## Next Steps

- **[Core Patterns](core-patterns.md)** - See symbols in context
- **[Examples](examples/orchestrator.md)** - Real-world usage
- **[Playground](playground.md)** - Experiment with symbols

Ready to use symbols? Try the [Playground](playground.md)!
