"""Utilities for generating DreamFusion prompts and launching training jobs."""
from __future__ import annotations

import math
import os
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, List, Literal, Optional

import numpy as np
import pandas as pd
from openai import BadRequestError, OpenAI

# Project level directories
SERVICE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SERVICE_DIR.parent
ROOT_DIR = BACKEND_DIR.parent
DATA_DIR = ROOT_DIR / "data"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "dreamfusion_outputs"
DEFAULT_DREAMFUSION_REPO = ROOT_DIR / "stable-dreamfusion"
API_ENV_FILE = ROOT_DIR / "api.env"

DatasetName = Literal["kepler", "k2", "tess", "custom"]


def _normalize_value(value: Any) -> Any:
    """Convert pandas/numpy values to JSON-serializable primitives."""

    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:  # pragma: no cover - defensive
        pass

    if isinstance(value, (float, int)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return float(value) if isinstance(value, float) else int(value)

    if isinstance(value, (np.generic,)):
        return _normalize_value(value.item())

    if hasattr(value, 'isoformat'):
        try:
            return value.isoformat()
        except TypeError:  # pragma: no cover - fallback
            pass

    return value


class DreamFusionError(RuntimeError):
    """Raised when DreamFusion orchestration fails."""


DATASET_PATTERNS: dict[DatasetName, str] = {
    "kepler": "cumulative_*.csv",
    "k2": "k2pandc_*.csv",
    "tess": "TOI_*.csv",
}

class ModelTarget(str, Enum):
    """Subject categories supported by the DreamFusion microservice."""

    PLANET = "planet"
    STAR = "star"


FEATURE_COLUMNS: dict[ModelTarget, list[tuple[str, str]]] = {
    ModelTarget.PLANET: [
        ("pl_name", "Planet name"),
        ("kepler_name", "System designation"),
        ("hostname", "Host star"),
        ("discoverymethod", "Discovery method"),
        ("disc_year", "Discovery year"),
        ("pl_orbper", "Orbital period (days)"),
        ("koi_period", "Orbital period (days)"),
        ("pl_orbsmax", "Semi-major axis (AU)"),
        ("pl_rade", "Planet radius (Earth radii)"),
        ("koi_prad", "Planet radius (Earth radii)"),
        ("pl_bmasse", "Planet mass (Earth masses)"),
        ("pl_eqt", "Equilibrium temperature (K)"),
        ("koi_teq", "Equilibrium temperature (K)"),
        ("pl_orbeccen", "Orbital eccentricity"),
        ("pl_insol", "Insolation flux (Earth=1)"),
        ("koi_insol", "Insolation flux (Earth=1)"),
        ("st_teff", "Host star temperature (K)"),
        ("st_rad", "Host star radius (Sol radii)"),
        ("st_mass", "Host star mass (Sol masses)"),
        ("st_met", "Host star metallicity [Fe/H]"),
        ("st_spectype", "Host star spectral type"),
        ("sy_dist", "System distance (pc)"),
        ("sy_vmag", "Visual magnitude"),
        ("sy_gaiamag", "Gaia G magnitude"),
    ],
    ModelTarget.STAR: [
        ("hostname", "Star name"),
        ("kepler_name", "System designation"),
        ("pl_name", "Known planet designation"),
        ("st_spectype", "Spectral type"),
        ("st_teff", "Effective temperature (K)"),
        ("st_rad", "Radius (Sol radii)"),
        ("st_mass", "Mass (Sol masses)"),
        ("st_met", "Metallicity [Fe/H]"),
        ("sy_dist", "Distance from Earth (pc)"),
        ("sy_vmag", "Visual magnitude"),
        ("sy_gaiamag", "Gaia G magnitude"),
        ("sy_kmag", "Infrared K magnitude"),
        ("disc_year", "Discovery year"),
    ],
}

NAME_COLUMNS: list[str] = ["pl_name", "kepler_name", "kepoi_name"]


def _load_openai_api_key() -> str:
    """Fetch the OpenAI API key either from the environment or from api.env."""

    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key

    if API_ENV_FILE.exists():
        for line in API_ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("OPENAI_API_KEY="):
                _, value = line.split("=", 1)
                value = value.strip().strip('"')
                if value:
                    os.environ.setdefault("OPENAI_API_KEY", value)
                    return value

    raise DreamFusionError(
        "OPENAI_API_KEY not configured. Export it or add it to api.env."
    )


@lru_cache(maxsize=3)
def _load_dataset(dataset: DatasetName) -> pd.DataFrame:
    """Read a dataset CSV into a DataFrame (comment-aware)."""

    if dataset == "custom":
        return pd.DataFrame()

    pattern = DATASET_PATTERNS.get(dataset)
    if not pattern:
        raise DreamFusionError(f"Unsupported dataset '{dataset}'.")

    files = sorted(DATA_DIR.glob(pattern))
    if not files:
        raise DreamFusionError(
            f"Dataset file matching pattern '{pattern}' not found in {DATA_DIR}."
        )

    # Use the most recent snapshot if multiple matches exist.
    csv_path = files[-1]
    return pd.read_csv(csv_path, comment="#", low_memory=False)


def _sanitize_workspace_name(name: str) -> str:
    """Create a filesystem-friendly workspace name."""

    safe = [c for c in name if c.isalnum() or c in ("-", "_")]
    sanitized = "".join(safe)
    if not sanitized:
        sanitized = "workspace"
    return sanitized.lower()


@dataclass
class PlanetRecord:
    dataset: DatasetName
    raw: dict[str, Any]
    custom_keys: set[str] | None = None

    @property
    def name(self) -> str:
        name = (
            self.raw.get("pl_name")
            or self.raw.get("kepler_name")
            or self.raw.get("hostname")
        )
        return str(name or "unknown")

    def json_ready(self) -> dict[str, Any]:
        return {key: _normalize_value(value) for key, value in self.raw.items()}

    def feature_summary(self, target: ModelTarget) -> dict[str, Any]:
        summary: dict[str, Any] = {}
        columns = FEATURE_COLUMNS[target]
        column_names = {column for column, _ in columns}

        for column, label in columns:
            if column not in self.raw:
                continue
            value = _normalize_value(self.raw[column])
            if value is None:
                continue
            if isinstance(value, float):
                summary[label] = round(value, 4)
            else:
                summary[label] = value

        extra_keys = (self.custom_keys or set()) - column_names
        for key in extra_keys:
            value = _normalize_value(self.raw.get(key))
            if value is None:
                continue
            label = key.replace("_", " ").strip().title() or key
            summary[label] = value
        return summary


class PlanetCatalog:
    """Provides lookup utilities for the exoplanet datasets."""

    def __init__(self) -> None:
        self._cached_examples: dict[DatasetName, PlanetRecord] = {}

    def get_planet(
        self,
        dataset: DatasetName,
        planet_name: Optional[str] = None,
    ) -> PlanetRecord:
        if dataset == "custom":
            raise DreamFusionError(
                "Dataset 'custom' does not contain catalog entries; provide characteristics explicitly."
            )
        df = _load_dataset(dataset)

        if planet_name:
            target = planet_name.lower()
            for name_column in NAME_COLUMNS:
                if name_column not in df.columns:
                    continue
                mask = df[name_column].astype(str).str.lower() == target
                if mask.any():
                    row = df[mask].iloc[0].fillna(pd.NA)
                    return PlanetRecord(dataset=dataset, raw=row.to_dict())
            raise DreamFusionError(
                f"Planet '{planet_name}' not found in the {dataset} dataset."
            )
        return self._pick_example(dataset, df)

    def _pick_example(
        self,
        dataset: DatasetName,
        df: pd.DataFrame,
    ) -> PlanetRecord:
        cached = self._cached_examples.get(dataset)
        if cached:
            return cached

        preferred_columns = ["pl_rade", "pl_bmasse", "pl_eqt", "pl_insol"]
        for _, row in df.iterrows():
            if any(not pd.isna(row.get(col)) for col in preferred_columns):
                record = PlanetRecord(dataset=dataset, raw=row.fillna(pd.NA).to_dict())
                self._cached_examples[dataset] = record
                return record

        row = df.iloc[0].fillna(pd.NA)
        record = PlanetRecord(dataset=dataset, raw=row.to_dict())
        self._cached_examples[dataset] = record
        return record

    def get_host(self, dataset: DatasetName, host_name: str) -> PlanetRecord:
        if dataset == "custom":
            raise DreamFusionError(
                "Dataset 'custom' does not contain host star entries; provide characteristics explicitly."
            )
        df = _load_dataset(dataset)
        if "hostname" not in df.columns:
            raise DreamFusionError(
                f"Dataset '{dataset}' does not contain host star information."
            )
        mask = df["hostname"].astype(str).str.lower() == host_name.lower()
        if not mask.any():
            raise DreamFusionError(
                f"Host star '{host_name}' not found in the {dataset} dataset."
            )
        row = df[mask].iloc[0].fillna(pd.NA)
        data = row.to_dict()
        data.setdefault("hostname", host_name)
        data.setdefault("pl_name", host_name)
        return PlanetRecord(dataset=dataset, raw=data)


class PromptBuilder:
    """Constructs DreamFusion-friendly prompts via the OpenAI Responses API."""

    def __init__(self, model: str = "gpt-5-mini", temperature: float = 0.6) -> None:
        self.model = model
        self.temperature = temperature
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            api_key = _load_openai_api_key()
            self._client = OpenAI(api_key=api_key)
        return self._client

    @staticmethod
    def _extract_output_text(response: Any) -> str:
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text

        collected: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text_value = getattr(content, "text", None)
                if text_value:
                    collected.append(text_value)
        return "\n\n".join(collected).strip()

    def build_prompt(self, planet: PlanetRecord, target: ModelTarget) -> str:
        summary = planet.feature_summary(target)
        formatted_lines = "\n".join(
            f"- {label}: {value}" for label, value in summary.items()
        )

        if target is ModelTarget.STAR:
            descriptor = "stellar"
            subject_line = (
                "Given the following stellar parameters, craft a vivid text prompt "
                "for Stable DreamFusion to produce a 3D model of this star. Describe "
                "its photosphere, prominences, coloration, magnetic activity, and "
                "any surrounding features in a single paragraph."
            )
        else:
            descriptor = "exoplanet"
            subject_line = (
                "Given the following exoplanet parameters, craft a vivid text prompt "
                "for Stable DreamFusion to produce a 3D model. Describe the planet's "
                "atmosphere, surface, coloration, lighting, and surroundings in a "
                "single paragraph."
            )

        system_message = (
            "You are an astrophysicist and 3D artist collaborating on Stable "
            "DreamFusion prompts."
        )
        user_message = (
            f"{subject_line} Avoid referencing photography or camera hardware. "
            f"{descriptor.capitalize()} parameters:\n"
            f"{formatted_lines}\n"
            "Focus on astronomical accuracy while keeping the description "
            "evocative and creative."
        )

        combined_input = f"{system_message}\n\n{user_message}"
        params = {
            "model": self.model,
            "input": combined_input,
        }
        if self.temperature is not None:
            params["temperature"] = self.temperature

        try:
            response = self.client.responses.create(**params)
        except BadRequestError as exc:
            message = str(exc).lower()
            if "temperature" in message and "unsupported" in message:
                params.pop("temperature", None)
                response = self.client.responses.create(**params)
            else:
                raise DreamFusionError(
                    "Failed to obtain prompt from OpenAI."
                ) from exc
        except Exception as exc:  # noqa: BLE001
            raise DreamFusionError(
                "Failed to obtain prompt from OpenAI."
            ) from exc

        prompt_text = self._extract_output_text(response)
        if not prompt_text:
            raise DreamFusionError("OpenAI did not return any prompt text.")
        return prompt_text


@dataclass
class DreamFusionJob:
    dataset: DatasetName
    planet: PlanetRecord
    target: ModelTarget
    prompt: str
    workspace: Path
    command: List[str]
    repo_path: Path
    dry_run: bool
    model: str
    use_cuda: bool

    def to_response_payload(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "planet": self.planet.json_ready(),
            "target": self.target.value,
            "prompt": self.prompt,
            "workspace": str(self.workspace),
            "command": self.command,
            "dry_run": self.dry_run,
            "model": self.model,
            "use_cuda": self.use_cuda,
        }


class DreamFusionService:
    """Coordinates prompt creation and DreamFusion training runs."""

    def __init__(
        self,
        repo_path: Path | None = None,
        output_dir: Path | None = None,
        model: str = "gpt-5-mini",
    ) -> None:
        self.repo_path = repo_path or DEFAULT_DREAMFUSION_REPO
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.default_model = model
        self._prompt_builders: dict[str, PromptBuilder] = {}
        self.catalog = PlanetCatalog()

    def prepare_job(
        self,
        dataset: DatasetName,
        planet_name: Optional[str] = None,
        host_name: Optional[str] = None,
        workspace_name: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        steps: Optional[int] = None,
        extra_args: Optional[Iterable[str]] = None,
        characteristics: Optional[dict[str, Any]] = None,
        llm_model: Optional[str] = None,
        target: ModelTarget = ModelTarget.PLANET,
        use_cuda: bool = True,
        dry_run: bool = True,
    ) -> DreamFusionJob:
        if not self.repo_path.exists():
            raise DreamFusionError(
                f"Stable DreamFusion repo not found at {self.repo_path}. Clone it first."
            )

        builder = self._get_prompt_builder(llm_model)
        planet = self._resolve_subject(
            dataset=dataset,
            planet_name=planet_name,
            host_name=host_name,
            target=target,
            characteristics=characteristics,
        )
        prompt = builder.build_prompt(planet, target)

        workspace_base = workspace_name or _sanitize_workspace_name(planet.name)
        workspace_path = self.output_dir / workspace_base
        workspace_path.parent.mkdir(parents=True, exist_ok=True)

        command = self._build_command(
            prompt=prompt,
            workspace=workspace_path,
            negative_prompt=negative_prompt,
            steps=steps,
            extra_args=extra_args,
            use_cuda=use_cuda,
        )

        return DreamFusionJob(
            dataset=dataset,
            planet=planet,
            target=target,
            prompt=prompt,
            workspace=workspace_path,
            command=command,
            repo_path=self.repo_path,
            dry_run=dry_run,
            model=builder.model,
            use_cuda=use_cuda,
        )

    def _build_command(
        self,
        prompt: str,
        workspace: Path,
        negative_prompt: Optional[str],
        steps: Optional[int],
        extra_args: Optional[Iterable[str]],
        use_cuda: bool,
    ) -> List[str]:
        args_list = list(extra_args) if extra_args else []
        cmd: List[str] = [
            sys.executable,
            "main.py",
            "--text",
            prompt,
            "--workspace",
            str(workspace),
        ]

        if use_cuda:
            cmd.append("-O")
        else:
            if not any(arg.startswith("--backbone") for arg in args_list):
                args_list.extend(["--backbone", "vanilla"])

        cmd.append("--save_mesh")

        if negative_prompt:
            cmd.extend(["--negative", negative_prompt])
        if steps is not None:
            cmd.extend(["--iters", str(steps)])
        if args_list:
            cmd.extend(args_list)
        return cmd

    def _resolve_subject(
        self,
        dataset: DatasetName,
        planet_name: Optional[str],
        host_name: Optional[str],
        target: ModelTarget,
        characteristics: Optional[dict[str, Any]],
    ) -> PlanetRecord:
        custom_data = characteristics or {}

        if dataset == "custom":
            if not custom_data:
                raise DreamFusionError(
                    "Provide 'characteristics' when using the custom dataset."
                )
            return self._make_custom_subject(
                dataset=dataset,
                name=host_name or planet_name,
                custom=custom_data,
                target=target,
            )

        base_record: PlanetRecord

        if target is ModelTarget.STAR and host_name:
            try:
                base_record = self.catalog.get_host(dataset, host_name)
            except DreamFusionError:
                if not custom_data:
                    raise
                return self._make_custom_subject(
                    dataset=dataset,
                    name=host_name,
                    custom=custom_data,
                    target=target,
                )
        elif planet_name:
            try:
                base_record = self.catalog.get_planet(dataset, planet_name)
            except DreamFusionError:
                if not custom_data:
                    raise
                return self._make_custom_subject(
                    dataset=dataset,
                    name=planet_name,
                    custom=custom_data,
                    target=target,
                )
        else:
            base_record = self.catalog.get_planet(dataset)

        if target is ModelTarget.STAR and host_name:
            base_record = self._ensure_star_name(base_record, host_name)

        if not custom_data:
            return base_record

        merged = base_record.raw.copy()
        merged.update(custom_data)
        return PlanetRecord(
            dataset=dataset,
            raw=merged,
            custom_keys=set(custom_data.keys()) or None,
        )

    def _make_custom_subject(
        self,
        dataset: DatasetName,
        name: Optional[str],
        custom: dict[str, Any],
        target: ModelTarget,
    ) -> PlanetRecord:
        data = custom.copy()
        custom_keys = set(data.keys())
        default_name = "Custom Star" if target is ModelTarget.STAR else "Custom Exoplanet"
        if "pl_name" not in data:
            data["pl_name"] = name or default_name
        if target is ModelTarget.STAR:
            data.setdefault("hostname", name or data.get("pl_name", default_name))
        if "kepler_name" not in data and "pl_name" in data:
            data.setdefault("kepler_name", data["pl_name"])
        return PlanetRecord(
            dataset=dataset, raw=data, custom_keys=custom_keys or None
        )

    @staticmethod
    def _ensure_star_name(record: PlanetRecord, host_name: str) -> PlanetRecord:
        raw = record.raw.copy()
        raw.setdefault("hostname", host_name)
        raw.setdefault("pl_name", host_name)
        return PlanetRecord(dataset=record.dataset, raw=raw, custom_keys=record.custom_keys)

    def _get_prompt_builder(self, llm_model: Optional[str]) -> PromptBuilder:
        target_model = llm_model or self.default_model
        builder = self._prompt_builders.get(target_model)
        if builder is None:
            builder = PromptBuilder(model=target_model)
            self._prompt_builders[target_model] = builder
        return builder

    def run_job(self, job: DreamFusionJob) -> subprocess.Popen[str]:
        if job.dry_run:
            raise DreamFusionError("Cannot execute a job marked as dry_run.")

        env = os.environ.copy()
        env.setdefault("PYTHONUNBUFFERED", "1")
        process = subprocess.Popen(  # noqa: S603, S607
            job.command,
            cwd=str(job.repo_path),
            env=env,
        )
        return process
