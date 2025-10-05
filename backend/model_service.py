"""
Model service for exoplanet classification predictions.
"""
import os
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from joblib import load

# Define feature columns expected by the model
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

# Feature mappings for different mission formats
FEATURE_MAPS = {
    "kepler": {
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
    "k2": {
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
    "tess": {
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
}

# Resolve default model directory relative to the project root so it works from any CWD
DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[1] / "assets" / "models"


def _resolve_model_dir() -> Path:
    """Determine the directory where trained models are stored."""
    env_dir = os.getenv("MODEL_DIR")
    if env_dir:
        return Path(env_dir).expanduser()
    return DEFAULT_MODEL_DIR


MODEL_DIR = _resolve_model_dir()
SHARED_IMPUTER_FILENAME = "shared_imputer.joblib"


class ModelService:
    """Service for loading models and making predictions."""

    def __init__(self, model_dir: Path | str = MODEL_DIR):
        self.model_dir = Path(model_dir).expanduser()
        self.models = {}
        self.imputer = None
        self._load_imputer()

    def _load_imputer(self):
        """Load the shared imputer."""
        imputer_path = self.model_dir / SHARED_IMPUTER_FILENAME
        if not imputer_path.exists():
            raise FileNotFoundError(
                f"Shared imputer not found at '{imputer_path}'. "
                "Please train models first using v1.py"
            )
        self.imputer = load(imputer_path)

    def _load_model(self, format_name: str):
        """Load a specific model if not already loaded."""
        if format_name not in self.models:
            model_path = self.model_dir / f"{format_name}_model.joblib"
            if not model_path.exists():
                raise FileNotFoundError(
                    f"Model for '{format_name}' not found at '{model_path}'. "
                    "Please train models first using v1.py"
                )
            self.models[format_name] = load(model_path)
        return self.models[format_name]

    def _safe_float(self, value) -> float:
        """Convert value to float, returning NaN for invalid values."""
        if value is None or value == "" or pd.isna(value):
            return np.nan
        try:
            return float(value)
        except (ValueError, TypeError):
            return np.nan

    def _prepare_features(self, df: pd.DataFrame, format_name: str) -> pd.DataFrame:
        """
        Transform raw dataframe to feature dataframe expected by the model.
        
        Args:
            df: Raw input dataframe with mission-specific column names
            format_name: Mission format ("kepler", "k2", or "tess")
            
        Returns:
            DataFrame with standardized feature columns
        """
        if format_name not in FEATURE_MAPS:
            raise ValueError(
                f"Unknown format '{format_name}'. "
                f"Available options: {list(FEATURE_MAPS.keys())}"
            )

        feature_map = FEATURE_MAPS[format_name]
        rows = []

        for _, raw_row in df.iterrows():
            record = {}
            for feature, source in feature_map.items():
                if source in raw_row:
                    record[feature] = self._safe_float(raw_row[source])
                else:
                    record[feature] = np.nan
            rows.append(record)

        return pd.DataFrame(rows, columns=FEATURE_COLUMNS)

    def _assign_class(
        self, probability: float, candidate_threshold: float, confirmed_threshold: float
    ) -> int:
        """
        Assign class based on probability and thresholds.
        
        Returns:
            0 - False Positive
            1 - Candidate
            2 - Confirmed
        """
        if probability >= confirmed_threshold:
            return 2
        if probability >= candidate_threshold:
            return 1
        return 0

    def predict(
        self, df: pd.DataFrame, format_name: str, hyperparams: dict
    ) -> pd.DataFrame:
        """
        Make predictions on input dataframe.
        
        Args:
            df: Input dataframe with raw mission data
            format_name: Mission format ("kepler", "k2", or "tess")
            hyperparams: Dictionary with keys:
                - candidate_threshold: float (threshold for candidate class)
                - confirmed_threshold: float (threshold for confirmed class)
                
        Returns:
            DataFrame with original data plus prediction columns:
                - predicted_class: int (0=FP, 1=Candidate, 2=Confirmed)
                - predicted_confidence: float (probability score 0-1)
        """
        # Validate hyperparameters
        candidate_threshold = hyperparams.get("candidate_threshold", 0.4)
        confirmed_threshold = hyperparams.get("confirmed_threshold", 0.7)

        if confirmed_threshold <= candidate_threshold:
            raise ValueError(
                "confirmed_threshold must be greater than candidate_threshold"
            )

        # Load the appropriate model
        model = self._load_model(format_name)

        # Prepare features
        features_df = self._prepare_features(df, format_name)

        # Impute missing values
        features_imputed = self.imputer.transform(features_df)

        # Get predictions
        probabilities = model.predict_proba(features_imputed)[:, 1]

        # Assign classes
        classes = [
            self._assign_class(p, candidate_threshold, confirmed_threshold)
            for p in probabilities
        ]

        # Create output dataframe
        result_df = df.copy()
        result_df["predicted_class"] = classes
        result_df["predicted_confidence"] = probabilities
        result_df["id"] = range(1, len(classes) + 1)

        return result_df


# Global model service instance
_model_service = None


def get_model_service() -> ModelService:
    """Get or create the global model service instance."""
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
    return _model_service
