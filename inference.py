import argparse
import os
from typing import Dict

import numpy as np
import pandas as pd
from joblib import load

from v1 import FEATURE_COLUMNS, MISSION_SPECS, iter_csv_records, safe_float

MODEL_DIR = "models"
SHARED_IMPUTER_FILENAME = "shared_imputer.joblib"


def resolve_spec(name: str):
    for spec in MISSION_SPECS:
        if spec.name == name:
            return spec
    raise ValueError(f"Unknown dataset '{name}'. Available options: {[spec.name for spec in MISSION_SPECS]}")


def load_inference_frame(csv_path: str, spec) -> pd.DataFrame:
    rows = []
    for raw in iter_csv_records(csv_path):
        record: Dict[str, float] = {
            feature: safe_float(raw.get(source)) for feature, source in spec.feature_map.items()
        }
        record["mission"] = spec.name
        disposition = (raw.get(spec.label_field) or "").strip() if spec.label_field in raw else ""
        record["disposition"] = disposition
        rows.append(record)

    columns = FEATURE_COLUMNS + ["mission", "disposition"]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns)


def assign_class(probability: float, candidate_threshold: float, confirmed_threshold: float) -> int:
    if probability >= confirmed_threshold:
        return 2
    if probability >= candidate_threshold:
        return 1
    return 0


def scored_filename(csv_path: str) -> str:
    stem, ext = os.path.splitext(csv_path)
    return f"{stem}_scored{ext or '.csv'}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run LightGBM inference and append class predictions plus confidence scores to CSV data."
    )
    parser.add_argument("dataset", help="Dataset key (e.g., kepler, k2, toi).")
    parser.add_argument("csv_path", help="Path to the CSV file to score.")
    parser.add_argument(
        "--candidate-threshold",
        type=float,
        default=0.4,
        help="Probability threshold for assigning the candidate class (default: 0.4).",
    )
    parser.add_argument(
        "--confirmed-threshold",
        type=float,
        default=0.7,
        help="Probability threshold for assigning the confirmed class (default: 0.7).",
    )
    parser.add_argument(
        "--output",
        help="Optional output path. Defaults to '<input>_scored.csv'.",
    )
    args = parser.parse_args()

    if args.confirmed_threshold <= args.candidate_threshold:
        raise ValueError("confirmed-threshold must be greater than candidate-threshold.")

    spec = resolve_spec(args.dataset)

    model_path = os.path.join(MODEL_DIR, f"{spec.name}_model.joblib")
    imputer_path = os.path.join(MODEL_DIR, SHARED_IMPUTER_FILENAME)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at '{model_path}'. Train models via v1.py first.")
    if not os.path.exists(imputer_path):
        raise FileNotFoundError(
            f"Shared imputer artifact not found at '{imputer_path}'. Train models via v1.py first."
        )

    model = load(model_path)
    imputer = load(imputer_path)

    raw_frame = pd.read_csv(args.csv_path, comment="#")
    features_frame = load_inference_frame(args.csv_path, spec)
    if features_frame.empty:
        print("No rows found in the provided CSV after parsing.")
        return

    features = imputer.transform(features_frame[FEATURE_COLUMNS])
    probabilities = model.predict_proba(features)[:, 1]

    classes = [
        assign_class(p, args.candidate_threshold, args.confirmed_threshold)
        for p in probabilities
    ]

    distance_to_candidate = np.abs(probabilities - args.candidate_threshold)
    distance_to_confirmed = np.abs(probabilities - args.confirmed_threshold)

    output_frame = raw_frame.copy()
    output_frame["predicted_class"] = classes
    output_frame["predicted_confidence"] = probabilities

    output_path = args.output or scored_filename(args.csv_path)
    output_frame.to_csv(output_path, index=False)
    print(
        f"Wrote scored data with appended columns to '{output_path}'."
        " Columns added: predicted_class, predicted_confidence."
    )


if __name__ == "__main__":
    main()
