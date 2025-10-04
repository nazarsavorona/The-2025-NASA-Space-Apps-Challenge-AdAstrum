import csv
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle

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

MODEL_DIR = "models"


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


def apply_candidate_weight(
    frame: pd.DataFrame,
    include_candidates: bool = True,
    candidate_weight: float = 0.35,
) -> pd.DataFrame:
    result = frame.copy()
    result["sample_weight"] = 1.0
    if include_candidates:
        result.loc[result["is_candidate"], "sample_weight"] = candidate_weight
    else:
        result = result[~result["is_candidate"]].copy()
    return result


def gather_datasets(
    include_candidates: bool = True,
    candidate_weight: float = 0.35,
) -> Tuple[Dict[str, pd.DataFrame], SimpleImputer]:
    mission_frames = load_all_missions()
    combined_features = pd.concat(
        [frame[FEATURE_COLUMNS] for frame in mission_frames.values()],
        ignore_index=True,
    )
    shared_imputer = SimpleImputer(strategy="median")
    shared_imputer.fit(combined_features)

    datasets: Dict[str, pd.DataFrame] = {}
    for name, frame in mission_frames.items():
        datasets[name] = apply_candidate_weight(frame, include_candidates, candidate_weight)
    combined_raw = pd.concat(mission_frames.values(), ignore_index=True)
    datasets["combined"] = apply_candidate_weight(combined_raw, include_candidates, candidate_weight)
    return datasets, shared_imputer


def prepare_splits(
    data: pd.DataFrame,
    include_candidates: bool = True,
    test_size: float = 0.2,
    imputer: Optional[SimpleImputer] = None,
) -> Dict[str, Optional[np.ndarray]]:
    certain = data[~data["is_candidate"]].copy()
    candidate = data[data["is_candidate"]].copy() if include_candidates else data.iloc[0:0]

    train_df, test_df = train_test_split(
        certain,
        test_size=test_size,
        stratify=certain["label"],
        random_state=RANDOM_SEED,
    )

    if imputer is None:
        fitted_imputer = SimpleImputer(strategy="median")
        fitted_imputer.fit(train_df[FEATURE_COLUMNS])
    else:
        fitted_imputer = imputer

    X_train_certain = fitted_imputer.transform(train_df[FEATURE_COLUMNS])
    X_test = fitted_imputer.transform(test_df[FEATURE_COLUMNS])
    y_train = train_df["label"].to_numpy(dtype=np.int64)
    y_test = test_df["label"].to_numpy(dtype=np.int64)
    w_train = np.ones_like(y_train, dtype=np.float32)

    X_candidate = None
    y_candidate = None
    w_candidate = None

    if include_candidates and not candidate.empty:
        X_candidate_tmp = fitted_imputer.transform(candidate[FEATURE_COLUMNS])
        y_candidate_tmp = candidate["label"].to_numpy(dtype=np.int64)
        w_candidate_tmp = candidate["sample_weight"].to_numpy(dtype=np.float32)
        if np.any(w_candidate_tmp > 0):
            X_train = np.vstack([X_train_certain, X_candidate_tmp])
            y_train = np.concatenate([y_train, y_candidate_tmp])
            w_train = np.concatenate([w_train, w_candidate_tmp])
        else:
            X_train = X_train_certain
        X_candidate = X_candidate_tmp
        y_candidate = y_candidate_tmp
        w_candidate = w_candidate_tmp
    else:
        X_train = X_train_certain

    X_train, y_train, w_train = shuffle(X_train, y_train, w_train, random_state=RANDOM_SEED)

    result: Dict[str, Optional[np.ndarray]] = {
        "train_df": train_df.reset_index(drop=True),
        "test_df": test_df.reset_index(drop=True),
        "candidate_df": candidate.reset_index(drop=True),
        "X_train": X_train.astype(np.float32),
        "y_train": y_train,
        "w_train": w_train.astype(np.float32),
        "X_test": X_test.astype(np.float32),
        "y_test": y_test,
        "X_candidate": None if X_candidate is None else X_candidate.astype(np.float32),
        "y_candidate": y_candidate,
        "w_candidate": None if w_candidate is None else w_candidate.astype(np.float32),
        "imputer": fitted_imputer,
    }
    return result


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
    include_candidates: bool,
    imputer: SimpleImputer,
) -> Dict[str, Dict[str, float]]:
    print(f"\n=== {dataset_name.upper()} DATASET ===")
    print_dataset_overview(dataset_name, data)
    try:
        prepared = prepare_splits(
            data,
            include_candidates=include_candidates,
            imputer=imputer,
        )
    except ValueError as exc:
        print(f"Skipping {dataset_name}: {exc}")
        return {}

    metrics_summary: Dict[str, Dict[str, float]] = {}

    lgb_model = train_lightgbm(
        prepared["X_train"], prepared["y_train"], prepared["w_train"]
    )
    if lgb_model is None:
        return metrics_summary

    lgb_test_probs = lgb_model.predict_proba(prepared["X_test"])[:, 1]
    metrics = compute_metrics(prepared["y_test"], lgb_test_probs)
    print_metrics("LightGBM", metrics)
    metrics_summary["LightGBM"] = metrics

    save_model_artifacts(dataset_name, lgb_model)

    candidate_df = prepared.get("candidate_df")
    candidate_features = prepared.get("X_candidate")
    if (
        candidate_df is not None
        and not candidate_df.empty
        and candidate_features is not None
    ):
        candidate_probs = lgb_model.predict_proba(candidate_features)[:, 1]
        top_indices = np.argsort(candidate_probs)[::-1][:5]
        print("Top candidate scores from LightGBM:")
        for idx in top_indices:
            row = candidate_df.iloc[idx]
            period = row["orbital_period"]
            radius = row["planet_radius"]
            period_txt = f"{period:.3f}" if pd.notna(period) else "nan"
            radius_txt = f"{radius:.3f}" if pd.notna(radius) else "nan"
            print(
                f"  {row['mission']:>6} {row['disposition']:<4} prob={candidate_probs[idx]:.3f} "
                f"period(days)={period_txt} radius(Rearth)={radius_txt}"
            )

    return metrics_summary


def main() -> None:
    include_candidates = True
    candidate_weight = 0.01

    datasets, shared_imputer = gather_datasets(
        include_candidates=include_candidates,
        candidate_weight=candidate_weight,
    )

    save_shared_imputer(shared_imputer)

    evaluation: Dict[str, Dict[str, float]] = {}
    ordered_names: List[str] = [spec.name for spec in MISSION_SPECS if spec.name in datasets]
    if "combined" in datasets:
        ordered_names.append("combined")

    for name in ordered_names:
        result = evaluate_dataset(
            name,
            datasets[name],
            include_candidates=include_candidates,
            imputer=shared_imputer,
        )
        evaluation[name] = result

    if evaluation:
        print("\n=== METRIC SUMMARY ===")
        for dataset_name, metrics_block in evaluation.items():
            if not metrics_block:
                continue
            print(f"{dataset_name}:")
            for model_name, metrics in metrics_block.items():
                print(
                    f"  {model_name:<12} accuracy={metrics['accuracy']:.3f} "
                    f"roc_auc={metrics['roc_auc']:.3f} avg_precision={metrics['avg_precision']:.3f} "
                    f"brier={metrics['brier']:.3f}"
                )


if __name__ == "__main__":
    main()
