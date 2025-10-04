from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold

try:  # pragma: no cover - optional dependency
    import lightgbm as lgb
except ImportError:  # pragma: no cover - optional dependency
    lgb = None

from .common import FEATURE_COLUMNS, MISSION_SPECS, MissionSpec, iter_csv_records, safe_float

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
warnings.filterwarnings("ignore")


@dataclass
class TrainConfig:
    datasets_dir: Path
    model_dir: Path
    include_candidates: bool = False
    n_splits: int = 5

    @classmethod
    def from_args(cls, *, datasets_dir: str, model_dir: str, include_candidates: bool, n_splits: int) -> "TrainConfig":
        return cls(
            datasets_dir=Path(datasets_dir),
            model_dir=Path(model_dir),
            include_candidates=include_candidates,
            n_splits=n_splits,
        )


def load_mission(spec: MissionSpec, datasets_dir: Path) -> pd.DataFrame:
    rows: List[Dict[str, float]] = []
    path = spec.resolve_path(datasets_dir)
    if not path.exists():
        raise FileNotFoundError(f"Mission dataset not found at '{path}'.")

    for raw in iter_csv_records(path):
        if spec.requires_default_flag:
            if (raw.get("default_flag") or "").strip() not in {"1", "TRUE", "true"}:
                continue
        label_value = (raw.get(spec.label_field) or "").strip().upper()
        if not label_value:
            continue
        if label_value in spec.positive_labels:
            label = 1
            is_candidate = False
        elif label_value in spec.negative_labels:
            label = 0
            is_candidate = False
        elif label_value in spec.candidate_labels:
            label = 1
            is_candidate = True
        else:
            continue
        record = {feature: safe_float(raw.get(source)) for feature, source in spec.feature_map.items()}
        if all(np.isnan(value) for value in record.values()):
            continue
        record["label"] = label
        record["is_candidate"] = is_candidate
        record["mission"] = spec.name
        record["disposition"] = label_value
        rows.append(record)

    columns = list(spec.feature_map.keys()) + ["label", "is_candidate", "mission", "disposition"]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns)


def load_all_missions(datasets_dir: Path) -> Dict[str, pd.DataFrame]:
    frames: Dict[str, pd.DataFrame] = {}
    for spec in MISSION_SPECS:
        frame = load_mission(spec, datasets_dir)
        if not frame.empty:
            frames[spec.name] = frame
    if not frames:
        raise RuntimeError("No data loaded; check file paths and formats.")
    return frames


def gather_datasets(
    datasets_dir: Path,
    include_candidates: bool = True,
) -> Tuple[Dict[str, pd.DataFrame], SimpleImputer]:
    mission_frames = load_all_missions(datasets_dir)

    filtered_frames: Dict[str, pd.DataFrame] = {}
    for name, frame in mission_frames.items():
        filtered = frame.copy()
        if not include_candidates:
            filtered = filtered[~filtered["is_candidate"]].copy()
        filtered_frames[name] = filtered

    feature_sources = [frame[FEATURE_COLUMNS] for frame in filtered_frames.values() if not frame.empty]
    if not feature_sources:
        raise RuntimeError("No data available to fit imputer; check dataset filtering.")

    combined_features = pd.concat(feature_sources, ignore_index=True)
    shared_imputer = SimpleImputer(strategy="median")
    shared_imputer.fit(combined_features)

    datasets: Dict[str, pd.DataFrame] = {name: frame for name, frame in filtered_frames.items()}
    combined_raw = pd.concat(filtered_frames.values(), ignore_index=True)
    datasets["combined"] = combined_raw
    return datasets, shared_imputer


def compute_metrics(y_true: np.ndarray, probabilities: np.ndarray) -> Dict[str, float]:
    preds = (probabilities >= 0.5).astype(int)
    return {
        "accuracy": accuracy_score(y_true, preds),
        "roc_auc": roc_auc_score(y_true, probabilities),
        "avg_precision": average_precision_score(y_true, probabilities),
        "brier": brier_score_loss(y_true, probabilities),
    }


def print_metrics(model_name: str, metrics: Dict[str, float]) -> None:
    print(
        f"{model_name:<12} accuracy={metrics['accuracy']:.3f} "
        f"roc_auc={metrics['roc_auc']:.3f} avg_precision={metrics['avg_precision']:.3f} "
        f"brier={metrics['brier']:.3f}"
    )


def train_lightgbm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    w_train: np.ndarray,
):
    if lgb is None:
        print("LightGBM is not installed; skipping.")
        return None

    model = lgb.LGBMClassifier(
        n_estimators=400,
        learning_rate=0.03,
        num_leaves=48,
        min_child_samples=40,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.0,
        reg_lambda=1.0,
        random_state=RANDOM_SEED,
        verbosity=-1,
        n_jobs=-1,
    )
    model.fit(X_train, y_train, sample_weight=w_train)
    return model


def save_model_artifacts(model_dir: Path, dataset_name: str, model) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / f"{dataset_name}_model.joblib"
    dump(model, model_path)
    print(f"Saved LightGBM model to '{model_path}'.")


def save_shared_imputer(model_dir: Path, imputer: SimpleImputer) -> Path:
    model_dir.mkdir(parents=True, exist_ok=True)
    imputer_path = model_dir / "shared_imputer.joblib"
    dump(imputer, imputer_path)
    print(f"Saved shared imputer to '{imputer_path}'.")
    return imputer_path


def print_dataset_overview(dataset_name: str, data: pd.DataFrame) -> None:
    total_rows = len(data)
    positives = int((data["label"] == 1).sum())
    negatives = int((data["label"] == 0).sum())
    candidates = int(data["is_candidate"].sum())
    print(
        f"Dataset '{dataset_name}': total={total_rows} positives={positives} "
        f"negatives={negatives} candidates={candidates}"
    )
    mission_stats = (
        data.groupby("mission")["is_candidate"].agg(["count", "sum"]).reset_index()
        if "mission" in data.columns
        else pd.DataFrame()
    )
    for _, row in mission_stats.iterrows():
        print(
            f"  {row['mission']:<6} total={int(row['count']):4d} "
            f"candidates={int(row['sum']):4d}"
        )


def evaluate_dataset(
    dataset_name: str,
    data: pd.DataFrame,
    model_dir: Path,
    shared_imputer: SimpleImputer,
    n_splits: int = 5,
) -> Dict[str, Dict[str, Dict[str, float]]]:
    print(f"\n=== {dataset_name.upper()} DATASET ===")
    print_dataset_overview(dataset_name, data)

    if data.empty:
        print(f"Skipping {dataset_name}: no rows available after filtering.")
        return {}

    if "is_candidate" in data.columns:
        certain = data[~data["is_candidate"]].copy()
    else:
        certain = data.copy()
    if certain.empty:
        print(f"Skipping {dataset_name}: no certain (non-candidate) rows found.")
        return {}

    label_counts = certain["label"].value_counts()
    if (label_counts < n_splits).any():
        print(
            f"Skipping {dataset_name}: not enough samples per class for {n_splits}-fold stratified CV."
        )
        return {}

    fold_metrics: List[Dict[str, float]] = []
    splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)

    for fold_idx, (train_idx, val_idx) in enumerate(
        splitter.split(certain[FEATURE_COLUMNS], certain["label"]),
        start=1,
    ):
        train_df = certain.iloc[train_idx].reset_index(drop=True)
        val_df = certain.iloc[val_idx].reset_index(drop=True)

        imputer = SimpleImputer(strategy="median")
        imputer.fit(train_df[FEATURE_COLUMNS])

        X_train = imputer.transform(train_df[FEATURE_COLUMNS])
        X_val = imputer.transform(val_df[FEATURE_COLUMNS])
        y_train = train_df["label"].to_numpy(dtype=np.int64)
        y_val = val_df["label"].to_numpy(dtype=np.int64)

        w_train = np.ones_like(y_train, dtype=np.float32)
        model = train_lightgbm(X_train, y_train, w_train)
        if model is None:
            return {}

        val_prob = model.predict_proba(X_val)[:, 1]
        metrics = compute_metrics(y_val, val_prob)
        fold_metrics.append(metrics)
        print_metrics(f"Fold {fold_idx}", metrics)

    aggregated_mean = {
        key: float(np.mean([m[key] for m in fold_metrics])) for key in fold_metrics[0]
    }
    aggregated_std = {
        key: float(np.std([m[key] for m in fold_metrics], ddof=0)) for key in fold_metrics[0]
    }

    print(
        "Average metrics over "
        f"{n_splits} folds: "
        f"accuracy={aggregated_mean['accuracy']:.3f}+/-{aggregated_std['accuracy']:.3f} "
        f"roc_auc={aggregated_mean['roc_auc']:.3f}+/-{aggregated_std['roc_auc']:.3f} "
        f"avg_precision={aggregated_mean['avg_precision']:.3f}+/-{aggregated_std['avg_precision']:.3f} "
        f"brier={aggregated_mean['brier']:.3f}+/-{aggregated_std['brier']:.3f}"
    )

    X_full = shared_imputer.transform(certain[FEATURE_COLUMNS])
    y_full = certain["label"].to_numpy(dtype=np.int64)
    w_full = np.ones_like(y_full, dtype=np.float32)
    final_model = train_lightgbm(X_full, y_full, w_full)
    if final_model is not None:
        save_model_artifacts(model_dir, dataset_name, final_model)

    return {
        "LightGBM": {
            "mean": aggregated_mean,
            "std": aggregated_std,
        }
    }


def train_models(config: TrainConfig) -> Dict[str, Dict[str, Dict[str, Dict[str, float]]]]:
    datasets, shared_imputer = gather_datasets(
        config.datasets_dir,
        include_candidates=config.include_candidates,
    )

    save_shared_imputer(config.model_dir, shared_imputer)

    evaluation: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {}
    ordered_names: List[str] = [spec.name for spec in MISSION_SPECS if spec.name in datasets]
    if "combined" in datasets:
        ordered_names.append("combined")

    for name in ordered_names:
        if datasets[name].empty:
            print(f"\n=== {name.upper()} DATASET ===")
            print(f"Skipping {name}: dataset is empty after filtering.")
            evaluation[name] = {}
            continue
        result = evaluate_dataset(
            name,
            datasets[name],
            model_dir=config.model_dir,
            shared_imputer=shared_imputer,
            n_splits=config.n_splits,
        )
        evaluation[name] = result

    if evaluation:
        print("\n=== METRIC SUMMARY ===")
        for dataset_name, models in evaluation.items():
            if not models:
                continue
            print(f"{dataset_name}:")
            for model_name, stats in models.items():
                mean_metrics = stats.get("mean", {})
                std_metrics = stats.get("std", {})
                if not mean_metrics:
                    continue
                print(
                    f"  {model_name:<12} accuracy={mean_metrics['accuracy']:.3f}+/-{std_metrics.get('accuracy', 0.0):.3f} "
                    f"roc_auc={mean_metrics['roc_auc']:.3f}+/-{std_metrics.get('roc_auc', 0.0):.3f} "
                    f"avg_precision={mean_metrics['avg_precision']:.3f}+/-{std_metrics.get('avg_precision', 0.0):.3f} "
                    f"brier={mean_metrics['brier']:.3f}+/-{std_metrics.get('brier', 0.0):.3f}"
                )

    return evaluation


def train_cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Train LightGBM models for exoplanet classification.")
    parser.add_argument(
        "--datasets-dir",
        default="assets/data",
        help="Directory containing mission CSV datasets (default: assets/data).",
    )
    parser.add_argument(
        "--model-dir",
        default="assets/models",
        help="Directory to persist trained models (default: assets/models).",
    )
    parser.add_argument(
        "--include-candidates",
        action="store_true",
        help="Include candidate labels during training (default: only confirmed/false positives).",
    )
    parser.add_argument(
        "--n-splits",
        type=int,
        default=5,
        help="Number of stratified CV folds (default: 5).",
    )

    args = parser.parse_args()
    config = TrainConfig.from_args(
        datasets_dir=args.datasets_dir,
        model_dir=args.model_dir,
        include_candidates=args.include_candidates,
        n_splits=args.n_splits,
    )

    train_models(config)


# Keep CLI compatibility when executed as a script.
if __name__ == "__main__":
    train_cli()
