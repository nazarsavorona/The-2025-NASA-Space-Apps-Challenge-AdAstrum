import csv
import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.utils import shuffle

try:
    import xgboost as xgb
except ImportError:  # pragma: no cover - optional dependency
    xgb = None

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover - optional dependency
    lgb = None

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

ENABLE_TORCH = os.environ.get("ENABLE_TORCH", "0") == "1"


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
    "period",
    "planet_radius",
    "stellar_teff",
    "stellar_radius",
    "stellar_logg",
    "insolation",
    "equilibrium_temp",
]

MISSION_SPECS = [
    MissionSpec(
        name="kepler",
        path="data/cumulative_2025.10.03_23.45.06.csv",
        label_field="koi_disposition",
        positive_labels=("CONFIRMED",),
        negative_labels=("FALSE POSITIVE",),
        candidate_labels=("CANDIDATE",),
        feature_map={
            "period": "koi_period",
            "planet_radius": "koi_prad",
            "stellar_teff": "koi_steff",
            "stellar_radius": "koi_srad",
            "stellar_logg": "koi_slogg",
            "insolation": "koi_insol",
            "equilibrium_temp": "koi_teq",
        },
    ),
    MissionSpec(
        name="k2",
        path="data/k2pandc_2025.10.03_23.45.12.csv",
        label_field="disposition",
        positive_labels=("CONFIRMED",),
        negative_labels=("FALSE POSITIVE", "REFUTED"),
        candidate_labels=("CANDIDATE",),
        feature_map={
            "period": "pl_orbper",
            "planet_radius": "pl_rade",
            "stellar_teff": "st_teff",
            "stellar_radius": "st_rad",
            "stellar_logg": "st_logg",
            "insolation": "pl_insol",
            "equilibrium_temp": "pl_eqt",
        },
        requires_default_flag=True,
    ),
    MissionSpec(
        name="tess",
        path="data/TOI_2025.10.03_23.44.18.csv",
        label_field="tfopwg_disp",
        positive_labels=("CP", "KP"),
        negative_labels=("FP", "FA"),
        candidate_labels=("PC", "APC"),
        feature_map={
            "period": "pl_orbper",
            "planet_radius": "pl_rade",
            "stellar_teff": "st_teff",
            "stellar_radius": "st_rad",
            "stellar_logg": "st_logg",
            "insolation": "pl_insol",
            "equilibrium_temp": "pl_eqt",
        },
    ),
]


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
) -> Dict[str, pd.DataFrame]:
    mission_frames = load_all_missions()
    datasets: Dict[str, pd.DataFrame] = {}
    for name, frame in mission_frames.items():
        datasets[name] = apply_candidate_weight(frame, include_candidates, candidate_weight)
    combined_raw = pd.concat(mission_frames.values(), ignore_index=True)
    datasets["combined"] = apply_candidate_weight(combined_raw, include_candidates, candidate_weight)
    return datasets


def prepare_splits(
    data: pd.DataFrame,
    include_candidates: bool = True,
    test_size: float = 0.2,
) -> Dict[str, Optional[np.ndarray]]:
    certain = data[~data["is_candidate"]].copy()
    candidate = data[data["is_candidate"]].copy() if include_candidates else data.iloc[0:0]

    train_df, test_df = train_test_split(
        certain,
        test_size=test_size,
        stratify=certain["label"],
        random_state=RANDOM_SEED,
    )

    imputer = SimpleImputer(strategy="median")
    imputer.fit(train_df[FEATURE_COLUMNS])

    X_train_certain = imputer.transform(train_df[FEATURE_COLUMNS])
    X_test = imputer.transform(test_df[FEATURE_COLUMNS])
    y_train = train_df["label"].to_numpy(dtype=np.int64)
    y_test = test_df["label"].to_numpy(dtype=np.int64)
    w_train = np.ones_like(y_train, dtype=np.float32)

    X_candidate = None
    y_candidate = None
    w_candidate = None

    if include_candidates and not candidate.empty:
        X_candidate_tmp = imputer.transform(candidate[FEATURE_COLUMNS])
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

    scaler = StandardScaler()
    scaler.fit(X_train)

    X_train_scaled = scaler.transform(X_train).astype(np.float32)
    X_test_scaled = scaler.transform(X_test).astype(np.float32)
    X_candidate_scaled = scaler.transform(X_candidate).astype(np.float32) if X_candidate is not None else None

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
        "X_train_scaled": X_train_scaled,
        "X_test_scaled": X_test_scaled,
        "X_candidate_scaled": X_candidate_scaled,
        "imputer": imputer,
        "scaler": scaler,
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


def show_candidate_scores(
    model_name: str,
    probabilities: Optional[np.ndarray],
    candidate_df: pd.DataFrame,
    top_k: int = 5,
) -> None:
    if probabilities is None or candidate_df.empty:
        return
    order = np.argsort(probabilities)[::-1][:top_k]
    print(f"Top {len(order)} candidate scores from {model_name}:")
    for idx in order:
        row = candidate_df.iloc[idx]
        period = row["period"]
        prad = row["planet_radius"]
        mission = row["mission"]
        disp = row["disposition"]
        period_txt = f"{period:.3f}" if pd.notna(period) else "nan"
        prad_txt = f"{prad:.3f}" if pd.notna(prad) else "nan"
        print(
            f"  {mission:>6} {disp:<4} prob={probabilities[idx]:.3f} "
            f"period(days)={period_txt} radius(Rearth)={prad_txt}"
        )


def print_sample_predictions(
    model_name: str,
    probabilities: np.ndarray,
    test_df: pd.DataFrame,
    count: int = 5,
) -> None:
    print(f"Sample {count} predictions from {model_name}:")
    limit = min(count, len(test_df))
    for i in range(limit):
        row = test_df.iloc[i]
        print(
            f"  true={row['label']} prob={probabilities[i]:.3f} "
            f"mission={row['mission']} disposition={row['disposition']}"
        )


def train_xgboost(X_train: np.ndarray, y_train: np.ndarray, w_train: np.ndarray):
    if xgb is None:
        print("XGBoost is not installed; skipping.")
        return None
    model = xgb.XGBClassifier(
        n_estimators=400,
        learning_rate=0.03,
        max_depth=5,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=RANDOM_SEED,
        tree_method="hist",
    )
    model.fit(X_train, y_train, sample_weight=w_train)
    return model


def train_lightgbm(X_train: np.ndarray, y_train: np.ndarray, w_train: np.ndarray):
    if lgb is None:
        print("LightGBM is not installed; skipping.")
        return None
    model = lgb.LGBMClassifier(
        n_estimators=600,
        learning_rate=0.03,
        num_leaves=48,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.0,
        reg_lambda=1.0,
        random_state=RANDOM_SEED,
    )
    model.fit(X_train, y_train, sample_weight=w_train)
    return model


def run_pytorch_pipeline(
    train_data: Tuple[np.ndarray, np.ndarray, np.ndarray],
    test_data: Tuple[np.ndarray, np.ndarray],
    candidate_scaled: Optional[np.ndarray],
    candidate_df: pd.DataFrame,
    test_df: pd.DataFrame,
    dataset_name: str,
) -> Optional[Dict[str, float]]:
    if not ENABLE_TORCH:
        print(
            f"PyTorch disabled for '{dataset_name}' (set ENABLE_TORCH=1 to enable in supported environments)."
        )
        return None
    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, Dataset
    except Exception as exc:  # pragma: no cover - optional path
        print(f"PyTorch unavailable for '{dataset_name}' ({exc}); skipping neural network.")
        return None

    torch.manual_seed(RANDOM_SEED)
    torch.set_num_threads(1)

    class WeightedTensorDataset(Dataset):
        def __init__(self, features: np.ndarray, labels: np.ndarray, weights: np.ndarray) -> None:
            self.features = torch.from_numpy(features.astype(np.float32))
            self.labels = torch.from_numpy(labels.astype(np.float32)).unsqueeze(1)
            self.weights = torch.from_numpy(weights.astype(np.float32)).unsqueeze(1)

        def __len__(self) -> int:
            return self.features.shape[0]

        def __getitem__(self, index: int):
            return self.features[index], self.labels[index], self.weights[index]

    class ExoplanetNet(nn.Module):
        def __init__(self, input_dim: int) -> None:
            super().__init__()
            self.layers = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.Linear(32, 1),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.layers(x)

    X_train_scaled, y_train, w_train = train_data
    X_test_scaled, y_test = test_data

    dataset = WeightedTensorDataset(X_train_scaled, y_train, w_train)
    loader = DataLoader(dataset, batch_size=64, shuffle=True, drop_last=False)
    model = ExoplanetNet(X_train_scaled.shape[1])
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
    criterion = nn.BCEWithLogitsLoss(reduction="none")

    model.train()
    for _ in range(80):
        for features, labels, weights in loader:
            optimizer.zero_grad()
            logits = model(features)
            loss = criterion(logits, labels)
            loss = (loss * weights).mean()
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        test_logits = model(torch.from_numpy(X_test_scaled.astype(np.float32)))
        test_probs = torch.sigmoid(test_logits).numpy().flatten()

    metrics = compute_metrics(y_test, test_probs)
    print_metrics("PyTorch NN", metrics)
    print_sample_predictions("PyTorch NN", test_probs, test_df)

    candidate_probs = None
    if candidate_scaled is not None and not candidate_df.empty:
        with torch.no_grad():
            candidate_logits = model(torch.from_numpy(candidate_scaled.astype(np.float32)))
            candidate_probs = torch.sigmoid(candidate_logits).numpy().flatten()
    show_candidate_scores("PyTorch NN", candidate_probs, candidate_df)
    return metrics


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
) -> Dict[str, Dict[str, float]]:
    print(f"\n=== {dataset_name.upper()} DATASET ===")
    print_dataset_overview(dataset_name, data)
    try:
        prepared = prepare_splits(data, include_candidates=include_candidates)
    except ValueError as exc:
        print(f"Skipping {dataset_name}: {exc}")
        return {}

    metrics_summary: Dict[str, Dict[str, float]] = {}

    xgb_model = train_xgboost(prepared["X_train"], prepared["y_train"], prepared["w_train"])
    if xgb_model is not None:
        xgb_test_probs = xgb_model.predict_proba(prepared["X_test"])[:, 1]
        metrics = compute_metrics(prepared["y_test"], xgb_test_probs)
        print_metrics("XGBoost", metrics)
        print_sample_predictions("XGBoost", xgb_test_probs, prepared["test_df"])
        candidate_probs = None
        if prepared["X_candidate"] is not None:
            candidate_probs = xgb_model.predict_proba(prepared["X_candidate"])[:, 1]
        show_candidate_scores("XGBoost", candidate_probs, prepared["candidate_df"])
        metrics_summary["XGBoost"] = metrics

    lgb_model = train_lightgbm(prepared["X_train"], prepared["y_train"], prepared["w_train"])
    if lgb_model is not None:
        lgb_test_probs = lgb_model.predict_proba(prepared["X_test"])[:, 1]
        metrics = compute_metrics(prepared["y_test"], lgb_test_probs)
        print_metrics("LightGBM", metrics)
        print_sample_predictions("LightGBM", lgb_test_probs, prepared["test_df"])
        candidate_probs = None
        if prepared["X_candidate"] is not None:
            candidate_probs = lgb_model.predict_proba(prepared["X_candidate"])[:, 1]
        show_candidate_scores("LightGBM", candidate_probs, prepared["candidate_df"])
        metrics_summary["LightGBM"] = metrics

    torch_metrics = run_pytorch_pipeline(
        (
            prepared["X_train_scaled"],
            prepared["y_train"].astype(np.float32),
            prepared["w_train"],
        ),
        (prepared["X_test_scaled"], prepared["y_test"]),
        prepared["X_candidate_scaled"],
        prepared["candidate_df"],
        prepared["test_df"],
        dataset_name,
    )
    if torch_metrics is not None:
        metrics_summary["PyTorch NN"] = torch_metrics

    return metrics_summary


def main() -> None:
    include_candidates = True
    candidate_weight = 0.35

    datasets = gather_datasets(
        include_candidates=include_candidates,
        candidate_weight=candidate_weight,
    )

    evaluation: Dict[str, Dict[str, float]] = {}
    ordered_names: List[str] = [spec.name for spec in MISSION_SPECS if spec.name in datasets]
    if "combined" in datasets:
        ordered_names.append("combined")

    for name in ordered_names:
        metrics = evaluate_dataset(name, datasets[name], include_candidates=include_candidates)
        evaluation[name] = metrics

    if evaluation:
        print("\n=== METRIC SUMMARY ===")
        for dataset_name, models in evaluation.items():
            if not models:
                continue
            print(f"{dataset_name}:")
            for model_name, metrics in models.items():
                print(
                    f"  {model_name:<12} accuracy={metrics['accuracy']:.3f} "
                    f"roc_auc={metrics['roc_auc']:.3f} avg_precision={metrics['avg_precision']:.3f} "
                    f"brier={metrics['brier']:.3f}"
                )


if __name__ == "__main__":
    main()
