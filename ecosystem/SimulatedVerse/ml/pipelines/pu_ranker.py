#!/usr/bin/env python3
import glob
import json
import os

import pandas as pd
from features import featurize_pu
from joblib import dump
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

DATA_DIR = os.environ.get("PU_TRACES","ml/data/traces")
OUT = "ml/models/pu_ranker.pkl"
os.makedirs("ml/models", exist_ok=True)

def load_traces():
    rows=[]
    for path in glob.glob(os.path.join(DATA_DIR,"*.jsonl")):
        with open(path,"r") as f:
            for line in f:
                try:
                    obj=json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("kind") != "PU":
                    continue
                y = 1 if obj.get("accepted",False) else 0
                x = featurize_pu(obj)
                x["y"]=y
                rows.append(x)
    return pd.DataFrame(rows) if rows else pd.DataFrame()

def main():
    df = load_traces()
    if df.empty or df["y"].nunique()<2:
        print("[ranker] not enough data yet; need both accepted and rejected PUs")
        return
    y=df["y"].values
    X=df.drop(columns=["y"]).values
    model=LogisticRegression(max_iter=500)
    model.fit(X,y)
    try:
        p=model.predict_proba(X)[:,1]
        auc=roc_auc_score(y,p)
        print(f"[ranker] trained AUC={auc:.3f} on {len(y)} PUs")
    except Exception as e:
        print("[ranker] eval skipped:", e)
    dump(model, OUT)
    print("[ranker] saved", OUT)

if __name__=="__main__":
    main()
