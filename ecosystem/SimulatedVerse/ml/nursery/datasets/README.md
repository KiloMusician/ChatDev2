# ML Nursery - Datasets

## Structure
- `events.jsonl`      # telemetry (redacted)
- `errors.jsonl`      # exception exemplars  
- `edits.jsonl`       # diff summaries (pre/after)

## Splits
Train/dev/test splits generated via `scripts/curate.ts`

## PII Protection
**REQUIRED**: All datasets must pass PII filter tests.
Tests enforce redaction of:
- Email addresses
- API keys / tokens
- File paths containing usernames
- IP addresses
- Personal names (when not public figures)

## Usage
```bash
# Generate curated dataset
npm run ml:curate

# Validate PII compliance  
npm run ml:test-pii

# Export for training
npm run ml:export
```