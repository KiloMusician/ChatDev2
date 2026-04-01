# ΞNuSyQ ML Spine

Real ML infrastructure for CoreLink Foundation autonomous development.

## 🧠 Infrastructure Status

- **ML Endpoints**: ✅ Operational (`/api/ml/train`, `/api/ml/rank`, `/api/ml/status`)
- **Training Pipeline**: ✅ Functional (Proposal Unit ranker with AUC=0.881)
- **Serving Layer**: ✅ Active (Node.js + Python integration)
- **Data Logging**: ✅ Automatic PU event capture
- **Legacy Harvesting**: ✅ Sparse repository checkout system

## 🎯 Live ML Pipeline

1. **PU Events** → Logged to `ml/data/traces/` 
2. **Training** → `/api/ml/train` produces `ml/models/pu_ranker.pkl`
3. **Ranking** → `/api/ml/rank` scores PUs for prioritization
4. **Integration** → Autonomous scheduler uses ML rankings

## 📊 Current Performance

- **Model**: Logistic Regression trained on 19 PUs
- **AUC**: 0.881 (excellent discrimination)
- **Features**: word_count, priority_level, task_type indicators
- **Fallback**: Heuristic scoring when model unavailable

## 🚀 Usage

```bash
# Train model on accumulated data
curl -X POST localhost:5000/api/ml/train

# Rank PU batch for prioritization  
curl -X POST -H "Content-Type: application/json" \
  -d '[{"title":"Fix bug","priority":"high","type":"TestPU"}]' \
  localhost:5000/api/ml/rank

# Check system status
curl localhost:5000/api/ml/status
```

## 🔄 Self-Improvement Loop

The system learns from usage patterns:
- PU acceptance/rejection automatically logged
- Model retrains as data accumulates  
- Ranking improves autonomous task prioritization
- Game progression generates better training data

## 🏗️ Architecture

```
ml/
├── data/           # Training data & snapshots
├── pipelines/      # Python ML training code  
├── models/         # Trained model artifacts
├── serving/        # Node.js ML API endpoints
└── notebooks/      # Analysis (optional)
```

This implements the Culture-Ship doctrine: *infrastructure-first ML that evolves through real usage*.