from __future__ import annotations

"""Heuristic categorisation of exoplanets into broad planet types.

The classifier compares a feature vector against handcrafted ranges for four
planet categories (Gas Giant, Neptune-like, Super-Earth, Terrestrial).  Each
feature is scored based on how far it falls outside the expected range; scores
are summed, so lower totals represent a closer match.  The first
category whose score stays below the configured thresholds is returned.

Example
-------
    >>> import pandas as pd
    >>> classifier = PlanetCategoryClassifier()
    >>> sample = {
    ...     "orbital_period": 12.4,
    ...     "transit_duration": 3.1,
    ...     "transit_depth": 0.004,
    ...     "impact_parameter": 0.2,
    ...     "eccentricity": 0.04,
    ...     "inclination": 88.7,
    ...     "planet_radius": 7.5,
    ...     "planet_equilibrium_temp": 900.0,
    ...     "insolation_flux": 1.8,
    ...     "stellar_temp": 5600.0,
    ...     "stellar_logg": 4.4,
    ...     "stellar_radius": 0.95,
    ...     "stellar_mass": 0.95,
    ...     "stellar_metallicity": 0.1,
    ... }
    >>> frame = pd.DataFrame([sample])
    >>> results = classifier.predict(frame)
    >>> results.loc[0, "predicted_category"]
    'Gas Giant'
"""

import math
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

import pandas as pd

from .common import FEATURE_COLUMNS

__all__ = [
    "FeatureRange",
    "CategoryMatch",
    "PlanetCategoryClassifier",
    "CATEGORY_SIGNATURES",
]


@dataclass(frozen=True)
class FeatureRange:
    """Inclusive numeric range with penalties for deviations."""

    lower: float
    upper: float
    weight: float = 1.0

    def evaluate(self, value: Optional[float]) -> Tuple[float, bool, bool]:
        """Return ``(score, in_range, is_missing)`` for ``value``.

        The score is the fractional distance from the valid interval scaled by
        the feature weight. It is zero when the value lies within the range and
        increases linearly as the value drifts away. Missing values contribute no
        penalty but are flagged so callers can react if needed.
        """

        try:
            numeric = float(value) if value is not None else math.nan
        except (TypeError, ValueError):
            numeric = math.nan

        if math.isnan(numeric):
            return 0.0, False, True

        width = self.upper - self.lower
        if width <= 0:
            width = max(abs(self.upper) + abs(self.lower), 1.0)

        if self.lower <= numeric <= self.upper:
            return 0.0, True, False

        if numeric < self.lower:
            distance = (self.lower - numeric) / width
        else:
            distance = (numeric - self.upper) / width
        return distance * self.weight, False, False


@dataclass(frozen=True)
class CategoryMatch:
    """Result of comparing features against a category signature."""

    name: str
    total_score: float


@dataclass(frozen=True)
class CategorySignature:
    """Expected feature ranges representing a single planet category."""

    name: str
    feature_ranges: Dict[str, FeatureRange]

    def score(self, features: Mapping[str, float]) -> CategoryMatch:
        total_score = 0.0

        for feature, spec in self.feature_ranges.items():
            value = features.get(feature)
            score, _, _ = spec.evaluate(value)
            total_score += score

        return CategoryMatch(name=self.name, total_score=total_score)


def range_from_bounds(
    lower: float,
    upper: float,
    *,
    weight: float = 1.0,
) -> FeatureRange:
    if math.isclose(lower, upper):
        spread = max(abs(lower) * 0.01, 1e-6)
        lower -= spread
        upper += spread
    return FeatureRange(lower=float(lower), upper=float(upper), weight=weight)


COMMON_FEATURES: Dict[str, FeatureRange] = {
    "impact_parameter": range_from_bounds(0.0, 1.2, weight=0.2),
    "eccentricity": range_from_bounds(0.0, 0.8, weight=0.3),
    "inclination": range_from_bounds(80.0, 100.0, weight=0.3),
    "stellar_temp": range_from_bounds(3000.0, 7500.0, weight=0.2),
    "stellar_logg": range_from_bounds(3.5, 5.0, weight=0.2),
    "stellar_radius": range_from_bounds(0.3, 1.7, weight=0.2),
    "stellar_mass": range_from_bounds(0.2, 1.5, weight=0.2),
    "stellar_metallicity": range_from_bounds(-0.7, 0.5, weight=0.1),
}


CATEGORY_FEATURES: Dict[str, Dict[str, FeatureRange]] = {
    "Gas Giant": {
        "orbital_period": range_from_bounds(2.0, 6000.0, weight=0.7),
        "transit_duration": range_from_bounds(2.0, 120.0, weight=0.5),
        "transit_depth": range_from_bounds(0.003, 0.05, weight=1.4),
        "planet_radius": range_from_bounds(6.0, 16.0, weight=3.0),
        "planet_equilibrium_temp": range_from_bounds(50.0, 1600.0, weight=1.0),
        "insolation_flux": range_from_bounds(0.0, 5.0, weight=0.8),
    },
    "Neptune-like": {
        "orbital_period": range_from_bounds(2.0, 2000.0, weight=0.7),
        "transit_duration": range_from_bounds(1.0, 60.0, weight=0.5),
        "transit_depth": range_from_bounds(5e-4, 4e-3, weight=1.2),
        "planet_radius": range_from_bounds(2.0, 6.0, weight=2.5),
        "planet_equilibrium_temp": range_from_bounds(40.0, 800.0, weight=0.9),
        "insolation_flux": range_from_bounds(0.0, 8.0, weight=0.7),
    },
    "Super-Earth": {
        "orbital_period": range_from_bounds(1.0, 400.0, weight=0.8),
        "transit_duration": range_from_bounds(0.5, 25.0, weight=0.6),
        "transit_depth": range_from_bounds(2e-4, 1.5e-3, weight=1.0),
        "planet_radius": range_from_bounds(1.5, 2.5, weight=2.2),
        "planet_equilibrium_temp": range_from_bounds(200.0, 1200.0, weight=0.9),
        "insolation_flux": range_from_bounds(0.2, 30.0, weight=0.8),
    },
    "Terrestrial": {
        "orbital_period": range_from_bounds(1.0, 800.0, weight=0.8),
        "transit_duration": range_from_bounds(0.5, 20.0, weight=0.6),
        "transit_depth": range_from_bounds(5e-5, 8e-4, weight=1.1),
        "planet_radius": range_from_bounds(0.3, 1.5, weight=2.4),
        "planet_equilibrium_temp": range_from_bounds(150.0, 700.0, weight=0.8),
        "insolation_flux": range_from_bounds(0.1, 10.0, weight=0.7),
    },
}


def build_category_signature(name: str, extra: Mapping[str, FeatureRange]) -> CategorySignature:
    feature_ranges = dict(COMMON_FEATURES)
    feature_ranges.update(extra)
    missing = [feature for feature in FEATURE_COLUMNS if feature not in feature_ranges]
    if missing:
        raise ValueError(f"Category '{name}' missing required feature ranges: {missing}")
    return CategorySignature(name=name, feature_ranges=feature_ranges)


CATEGORY_SIGNATURES: Tuple[CategorySignature, ...] = tuple(
    build_category_signature(name, features) for name, features in CATEGORY_FEATURES.items()
)


class PlanetCategoryClassifier:
    """Assign the closest matching planet category based on feature ranges.

    Matches are ordered by total score, which is the sum of each feature's
    fractional distance outside its allowed interval. Lower scores indicate
    closer agreement with the category signature. The ``predict`` method works
    on DataFrames and appends the predicted category plus score for every row.
    This classifier now always assigns the best category (no unclassified rows),
    while still returning the score for reference.
    """

    def __init__(self, signatures: Optional[Sequence[CategorySignature]] = None) -> None:
        self._signatures: Tuple[CategorySignature, ...] = tuple(signatures or CATEGORY_SIGNATURES)
        self._feature_names = {feature for signature in self._signatures for feature in signature.feature_ranges}

        missing = [feature for feature in FEATURE_COLUMNS if feature not in self._feature_names]
        if missing:
            raise ValueError(f"Signatures missing required features: {missing}")

    @property
    def feature_names(self) -> Iterable[str]:
        return self._feature_names

    def rank(self, features: Mapping[str, float]) -> list[CategoryMatch]:
        matches = [signature.score(features) for signature in self._signatures]
        matches.sort(key=lambda match: match.total_score)
        return matches

    def predict_row(
        self,
        features: Mapping[str, float],
        *,
        max_total_score: float = 6.0,
    ) -> Optional[CategoryMatch]:
        """Return the best category match for a single feature mapping.

        Note: This implementation always returns the top-ranked category,
        regardless of ``max_total_score``. The parameter is retained for
        backward compatibility but is not used to filter results.
        """
        ranked = self.rank(features)
        return ranked[0] if ranked else None

    def predict(
        self,
        frame: pd.DataFrame,
        *,
        max_total_score: float = 6.0,
        category_column: str = "predicted_category",
        score_column: str = "category_score",
    ) -> pd.DataFrame:
        missing = [feature for feature in FEATURE_COLUMNS if feature not in frame.columns]
        if missing:
            raise ValueError(f"Missing required feature columns: {missing}")

        # Apply light preprocessing/normalization to handle unit mismatches
        # commonly found in mission catalogs (e.g., Kepler transit depth in ppm).
        norm = self.normalize_frame(frame)

        predictions = []
        scores = []
        for _, row in norm.iterrows():
            match = self.predict_row(row, max_total_score=max_total_score)
            if match is None:
                predictions.append(None)
                scores.append(float("inf"))
            else:
                predictions.append(match.name)
                scores.append(match.total_score)

        result = norm.copy()
        result[category_column] = predictions
        result[score_column] = scores
        return result

    def explain(self, features: Mapping[str, float]) -> Dict[str, CategoryMatch]:
        return {match.name: match for match in self.rank(features)}

    def normalize_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Return a shallow-normalized copy of feature columns in ``frame``.

        - transit_depth: auto-detect likely units from distribution and convert
          ppm→fraction (/1e6) or percent→fraction (/100). If already fractional,
          leave unchanged. Negative values are clipped to 0.
        - Basic physical clipping for a subset of features to avoid pathological
          scores: non-negativity for several scale variables; hard caps for
          eccentricity and impact parameter.
        """
        df = frame.copy()

        # Transit depth unit normalization
        if "transit_depth" in df.columns:
            depth = pd.to_numeric(df["transit_depth"], errors="coerce")
            q95 = depth.quantile(0.95)
            if pd.notna(q95):
                if q95 > 10:  # likely ppm
                    depth = depth / 1_000_000.0
                elif q95 > 1:  # likely percent
                    depth = depth / 100.0
            df["transit_depth"] = depth.clip(lower=0.0)

        # Non-negative clipping on a few obviously positive features
        for col in ("orbital_period", "transit_duration", "insolation_flux", "planet_radius"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").clip(lower=0.0)

        if "impact_parameter" in df.columns:
            df["impact_parameter"] = pd.to_numeric(df["impact_parameter"], errors="coerce").clip(lower=0.0, upper=1.5)

        if "eccentricity" in df.columns:
            df["eccentricity"] = pd.to_numeric(df["eccentricity"], errors="coerce").clip(lower=0.0, upper=0.99)

        return df
