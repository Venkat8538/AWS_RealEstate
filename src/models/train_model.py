import argparse
import os
import glob
import json
import pandas as pd
import xgboost as xgb

TRAIN_CHANNEL = "/opt/ml/input/data/train"
MODEL_DIR = "/opt/ml/model"

def parse_args():
    p = argparse.ArgumentParser()

    # XGBoost hyperparameters (must match what you pass from SageMaker)
    p.add_argument("--objective", type=str, default="reg:squarederror")
    p.add_argument("--num_round", type=int, default=100)
    p.add_argument("--max_depth", type=int, default=5)
    p.add_argument("--eta", type=float, default=0.2)
    p.add_argument("--gamma", type=float, default=4.0)
    p.add_argument("--min_child_weight", type=float, default=6.0)
    p.add_argument("--subsample", type=float, default=0.8)
    p.add_argument("--verbosity", type=int, default=1)

    # Data options
    p.add_argument("--target", type=str, default="Price",
                   help="Name of the target column in the CSVs")
    return p.parse_args()

def load_train_dataframe(train_dir: str, target_col: str) -> xgb.DMatrix:
    csvs = sorted(glob.glob(os.path.join(train_dir, "*.csv")))
    if not csvs:
        raise FileNotFoundError(f"No CSV files found under {train_dir}")

    # Concatenate all CSVs; header is OK in script mode
    dfs = []
    for path in csvs:
        df = pd.read_csv(path)
        if target_col not in df.columns:
            raise ValueError(f"Target column '{target_col}' not found in {path}. "
                             f"Columns present: {list(df.columns)}")
        dfs.append(df)
    data = pd.concat(dfs, ignore_index=True)

    y = data[target_col]
    X = data.drop(columns=[target_col])

    # Save feature names for later use
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(os.path.join(MODEL_DIR, "feature_names.json"), "w") as f:
        json.dump(list(X.columns), f)

    dtrain = xgb.DMatrix(X, label=y, feature_names=list(X.columns))
    return dtrain

def main():
    args = parse_args()
    print(">>> Received hyperparameters:", vars(args))

    dtrain = load_train_dataframe(TRAIN_CHANNEL, args.target)

    # Train
    params = {
        "objective": args.objective,
        "max_depth": args.max_depth,
        "eta": args.eta,
        "gamma": args.gamma,
        "min_child_weight": args.min_child_weight,
        "subsample": args.subsample,
        "verbosity": args.verbosity,
    }
    print(">>> XGBoost params:", params)
    model = xgb.train(params, dtrain, num_boost_round=args.num_round)

    # Save model — SageMaker will package everything in /opt/ml/model into model.tar.gz
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_model(os.path.join(MODEL_DIR, "xgboost-model"))
    print("✅ Saved model to /opt/ml/model/xgboost-model")

if __name__ == "__main__":
    main()
