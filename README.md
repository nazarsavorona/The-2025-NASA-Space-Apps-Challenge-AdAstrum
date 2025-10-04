# NASA Space Apps Challenge – AdAstrum

Tools for training and serving exoplanet classification models used by the AdAstrum project.

## Prerequisites
- Python 3.11 or newer
- CSV mission datasets placed under the directory you supply via `--datasets-dir` (defaults to `assets/data`)

Create a virtual environment and install the AI requirements:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Training Models
```bash
python train.py \
  --datasets-dir assets/data \
  --model-dir assets/models \
  --n-splits 5
```

Key options:
- `--datasets-dir`: where the mission CSV files (e.g., `kepler.csv`, `k2.csv`, `tess.csv`) live.
- `--model-dir`: output directory for LightGBM models and the shared imputer.
- `--include-candidates`: include mission candidate labels during training (disabled by default).
- `--n-splits`: number of stratified CV folds used when evaluating models (default `5`).

Trained artifacts are written to `<model-dir>/<mission>_model.joblib` and `shared_imputer.joblib`.

## Running Inference
Use the `inference.py` wrapper to score new CSV files:
```bash
python inference.py kepler path/to/kepler_sample.csv \
  --model-dir assets/models \
  --candidate-threshold 0.4 \
  --confirmed-threshold 0.7 \
  --output scored.csv
```
The script appends `predicted_class` (0 = false positive, 1 = candidate, 2 = confirmed) and `predicted_confidence` probability columns. When `--output` is omitted, results are saved alongside the source file as `<name>_scored.csv`.

## Backend API 
To run the FastAPI backend locally:
```bash
PYTHONPATH=backend uvicorn main:app --reload --host 0.0.0.0 --port 8000
```