# SNS Training Data - October 2024

## Summary

**Total Examples Created: 3,092**

Created for training a 3B model with **plain, universal language** focused on everyday scenarios that a smaller model can understand and generalize.

## Distribution by Category

### 1. Context-Aware Queries (1,000 examples)
**Files: 31-38, 47-51**

Pronouns, continuations, references, and everyday context:
- "Show me more like this"
- "Add them all up"
- "What's for breakfast?"
- "Water the thirsty ones"
- "Track my run"

**Focus**: Natural language with implicit context, teaching the model to handle "it", "them", "that", continuations like "then", "also", "and"

---

### 2. Multi-Intent/Complex Queries (900 examples)
**Files: 39-43, 53-55**

Multiple actions in one request across diverse life domains:
- "Find recipes with these ingredients and save the healthy ones"
- "Check calendar and plan commute"
- "Book appointment and set reminder"
- "Preheat oven and set timer"
- "Turn on lights and start coffee"

**Focus**: Real-world multi-step tasks covering:
- Home & family life
- Shopping & errands
- Health & fitness
- Travel & transportation
- Food & cooking
- Entertainment & hobbies
- Work & productivity

---

### 3. Ambiguous/Underspecified Queries (400 examples)
**Files: 44-46, 52**

Vague queries requiring inference:
- "Show me the things"
- "Make it better"
- "Fix the problem"
- "What's trending?"
- "Is it worth it?"

**Focus**: Teaching the model to:
- Infer missing context
- Ask clarifying questions
- Use defaults intelligently
- Handle one-word commands

---

### 4. Edge Cases (500 examples)
**Files: 56-60**

Boundary conditions, extreme values, format issues:
- Empty inputs, null values
- Out of bounds indices
- Invalid formats (email, phone, dates)
- Special characters, Unicode
- File size limits
- Number boundaries (negative, zero, infinity)
- Data type mismatches

**Focus**: Robust handling of real-world messy data

---

### 5. Error Handling (200 examples)
**Files: 61-62**

Error recovery and graceful degradation:
- Retry logic with backoff
- Fallback to cached data
- Circuit breaker patterns
- Validation errors
- Network failures
- Transaction rollbacks
- Service unavailable scenarios

**Focus**: Teaching the model to handle failures gracefully

---

## Design Principles

✅ **Plain Language**: Avoided technical jargon a 3B model might not know
✅ **Universal Scenarios**: Everyday situations anyone can relate to  
✅ **Diverse Domains**: 
   - Home (cooking, cleaning, maintenance)
   - Family (kids, pets, relationships)
   - Health (fitness, medicine, wellness)
   - Social (friends, events, communication)
   - Finance (shopping, budgets, payments)
   - Travel (flights, hotels, navigation)
   - Entertainment (movies, music, games, books)
   - Work (jobs, productivity)

✅ **Generalizable**: Patterns the model can apply to similar scenarios
✅ **Context-Rich**: Real conversational patterns with pronouns and references

---

## File Organization

```
data/training/
├── 01-30: Original examples (300 examples)
├── 31-38: Context-aware batch 1 (500 examples)
├── 39-43: Multi-intent original (500 examples) 
├── 44-46: Ambiguous original (300 examples)
├── 47-51: Context-aware batch 2 (500 examples)
├── 52: Ambiguous completion (100 examples)
├── 53-55: Multi-intent batch 2 (400 examples)
├── 56-60: Edge cases (500 examples)
└── 61-62: Error handling (200 examples)
```

---

## Training Recommendations

1. **Quality over quantity achieved**: 3,092 diverse, high-quality examples
2. **Balanced coverage**: Each category well-represented
3. **Plain language**: 3B model can understand and generalize
4. **Real-world focus**: Everyday scenarios vs. technical edge cases

### Suggested Training Approach

1. Start with **context-aware + multi-intent** (core capabilities)
2. Add **ambiguous** (handling vague requests)
3. Mix in **edge cases** (robustness)
4. Include **error handling** (graceful failures)

### Expected Improvements

- Better handling of pronouns and context
- Multi-step request understanding
- Ambiguity resolution
- Robust error handling
- More human-like SNS generation

---

**Created**: October 13, 2024
**Model Target**: 3B parameters (Llama 3.2, Phi, Qwen)
**Format**: JSONL (one example per line)
**SNS Version**: v1.0

