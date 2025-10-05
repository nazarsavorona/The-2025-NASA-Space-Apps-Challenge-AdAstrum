# NASA Space Apps Challenge – AdAstrum

Full‑stack application for exoplanet classification that combines production‑ready machine learning with an interactive Next.js frontend.

## Overview

- Backend (Python/FastAPI): model training, inference, and a REST API
- Frontend (Next.js): interactive UI for data exploration and results
- Models: LightGBM-based shared classifier for Kepler, K2/TOI, and TESS

---

## Backend (AI Models & API)

### Prerequisites
- Python 3.11+
- CSV mission datasets located under the directory passed via `--datasets-dir` (defaults to `assets/data`)

Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Train Models
```bash
python train.py \
  --datasets-dir assets/data \
  --model-dir assets/models \
  --n-splits 5
```

Key options:
- `--datasets-dir`: location of mission CSVs (e.g., `kepler.csv`, `k2.csv`, `tess.csv`).
- `--model-dir`: output directory for the shared LightGBM model and preprocessors.
- `--include-candidates`: include candidate labels during training (off by default).
- `--n-splits`: number of stratified CV folds (default: `5`).

Artifacts are written to `<model-dir>/shared_model.joblib` and `<model-dir>/shared_preprocessors.joblib`.

### Run Inference (CLI)
Score new CSV files via `inference.py`:
```bash
python inference.py kepler path/to/kepler_sample.csv \
  --model-dir assets/models \
  --candidate-threshold 0.4 \
  --confirmed-threshold 0.7 \
  --output scored.csv
```
The script appends `predicted_class` (0 = false positive, 1 = candidate, 2 = confirmed) and `predicted_confidence` columns. If `--output` is omitted, results are saved as `<name>_scored.csv` alongside the input file.

### Run the API
From the repository root:
```bash
PYTHONPATH=backend uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or via Docker Compose:
```bash
docker-compose up
```

---

## Frontend (Next.js)

This app uses the Next.js App Router and was bootstrapped with `create-next-app`.

### Development
```bash
npm install
npm run dev
# or: yarn dev / pnpm dev / bun dev
```
Open http://localhost:3000 to view the UI. Edit `app/page.js` to iterate; the page hot‑reloads.

### Build
```bash
npm run build && npm start
```

Deployment guidance: https://nextjs.org/docs/app/building-your-application/deploying

---

## Contributing

This project was developed for the 2025 NASA Space Apps Challenge.