import csv
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover - optional dependency
    lgb = None

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

import warnings
warnings.filterwarnings("ignore")

from joblib import dump


@dataclass
class MissionSpec:
    name: str
    path: str
    label_field: str
    positive_labels: Sequence[str]
    negative_labels: Sequence[str]
    candidate_labels: Sequence[str]
    feature_map: Dict[str, str]
    requires_default_flag: bool = False


FEATURE_COLUMNS = [
    "orbital_period",
    "transit_duration",
    "transit_depth",
    "impact_parameter",
    "eccentricity",
    "inclination",
    "planet_radius",
    "planet_equilibrium_temp",
    "insolation_flux",
    "stellar_temp",
    "stellar_logg",
    "stellar_radius",
    "stellar_mass",
    "stellar_metallicity",
]

MISSION_SPECS = [
    MissionSpec(
        name="kepler",
        path="data/kepler.csv",
        label_field="koi_disposition",
        positive_labels=("CONFIRMED",),
        negative_labels=("FALSE POSITIVE",),
        candidate_labels=("CANDIDATE",),
        feature_map={
            "orbital_period": "koi_period",
            "transit_duration": "koi_duration",
            "transit_depth": "koi_depth",
            "impact_parameter": "koi_impact",
            "eccentricity": "koi_eccen",
            "inclination": "koi_incl",
            "planet_radius": "koi_prad",
            "planet_equilibrium_temp": "koi_teq",
            "insolation_flux": "koi_insol",
            "stellar_temp": "koi_steff",
            "stellar_logg": "koi_slogg",
            "stellar_radius": "koi_srad",
            "stellar_mass": "koi_smass",
            "stellar_metallicity": "koi_smet",
        },
    ),
    MissionSpec(
        name="k2",
        path="data/k2.csv",
        label_field="disposition",
        positive_labels=("CONFIRMED",),
        negative_labels=("FALSE POSITIVE", "REFUTED"),
        candidate_labels=("CANDIDATE",),
        feature_map={
            "orbital_period": "pl_orbper",
            "transit_duration": "pl_trandur",
            "transit_depth": "pl_trandep",
            "impact_parameter": "pl_imppar",
            "eccentricity": "pl_orbeccen",
            "inclination": "pl_orbincl",
            "planet_radius": "pl_rade",
            "planet_equilibrium_temp": "pl_eqt",
            "insolation_flux": "pl_insol",
            "stellar_temp": "st_teff",
            "stellar_logg": "st_logg",
            "stellar_radius": "st_rad",
            "stellar_mass": "st_mass",
            "stellar_metallicity": "st_met",
        },
        requires_default_flag=True,
    ),
    MissionSpec(
        name="toi",
        path="data/tess.csv",
        label_field="tfopwg_disp",
        positive_labels=("CP", "KP"),
        negative_labels=("FP", "FA"),
        candidate_labels=("PC", "APC"),
        feature_map={
            "orbital_period": "pl_orbper",
            "transit_duration": "pl_trandur",
            "transit_depth": "pl_trandep",
            "impact_parameter": "pl_imppar",
            "eccentricity": "pl_orbeccen",
            "inclination": "pl_orbincl",
            "planet_radius": "pl_rade",
            "planet_equilibrium_temp": "pl_eqt",
            "insolation_flux": "pl_insol",
            "stellar_temp": "st_teff",
            "stellar_logg": "st_logg",
            "stellar_radius": "st_rad",
            "stellar_mass": "st_mass",
            "stellar_metallicity": "st_met",
        },
    ),
]

MODEL_DIR = "./assets/models"


def iter_csv_records(path: str) -> Iterable[Dict[str, str]]:
    with open(path, newline="") as handle:
        header: Optional[List[str]] = None
        for line in handle:
            if line.startswith("#"):
                continue
            header = [col.strip() for col in line.strip().split(",")]
            break
        if not header:
            return
        reader = csv.DictReader(handle, fieldnames=header)
        for row in reader:
            yield {key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()}


def safe_float(value: Optional[str]) -> float:
    if value is None or value == "":
        return np.nan
    try:
        return float(value)
    except ValueError:
        return np.nan


def load_mission(spec: MissionSpec) -> pd.DataFrame:
    rows: List[Dict[str, float]] = []
    for raw in iter_csv_records(spec.path):
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


def load_all_missions() -> Dict[str, pd.DataFrame]:
    frames: Dict[str, pd.DataFrame] = {}
    for spec in MISSION_SPECS:
        frame = load_mission(spec)
        if not frame.empty:
            frames[spec.name] = frame
    if not frames:
        raise RuntimeError("No data loaded; check file paths and formats.")
    return frames


def gather_datasets(include_candidates: bool = True) -> Tuple[Dict[str, pd.DataFrame], SimpleImputer]:
    mission_frames = load_all_missions()

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

    # Fixed hyperparameters chosen from prior grid search on the combined dataset.
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


def save_model_artifacts(dataset_name: str, model) -> None:
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, f"{dataset_name}_model.joblib")
    dump(model, model_path)
    print(f"Saved LightGBM model to '{model_path}'.")


def save_shared_imputer(imputer: SimpleImputer) -> str:
    os.makedirs(MODEL_DIR, exist_ok=True)
    imputer_path = os.path.join(MODEL_DIR, "shared_imputer.joblib")
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

    # Train final model on all certain rows using the shared imputer for inference.
    X_full = shared_imputer.transform(certain[FEATURE_COLUMNS])
    y_full = certain["label"].to_numpy(dtype=np.int64)
    w_full = np.ones_like(y_full, dtype=np.float32)
    final_model = train_lightgbm(X_full, y_full, w_full)
    if final_model is not None:
        save_model_artifacts(dataset_name, final_model)

    return {
        "LightGBM": {
            "mean": aggregated_mean,
            "std": aggregated_std,
        }
    }


def main() -> None:
    include_candidates = False

    datasets, shared_imputer = gather_datasets(
        include_candidates=include_candidates,
    )

    save_shared_imputer(shared_imputer)

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
            shared_imputer=shared_imputer,
            n_splits=5,
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


if __name__ == "__main__":
    main()
