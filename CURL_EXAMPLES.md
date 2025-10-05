# AdAstrum API - curl Test Commands

## Health Check
```bash
curl http://localhost:8000/
```

## Single Prediction (Kepler format)
```bash
curl -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{
    "format": "kepler",
    "data": [
      {
        "koi_period": 10.5,
        "koi_prad": 2.5,
        "koi_teq": 500,
        "koi_insol": 100,
        "koi_steff": 5500,
        "koi_slogg": 4.5,
        "koi_srad": 1.0
      }
    ],
    "hyperparams": {
      "candidate_threshold": 0.4,
      "confirmed_threshold": 0.7
    }
  }'
```

## Multiple Predictions (Kepler format)
```bash
curl -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{
    "format": "kepler",
    "data": [
      {
        "koi_period": 10.5,
        "koi_prad": 2.5,
        "koi_teq": 500,
        "koi_insol": 100,
        "koi_steff": 5500,
        "koi_slogg": 4.5,
        "koi_srad": 1.0
      },
      {
        "koi_period": 5.2,
        "koi_prad": 1.2,
        "koi_teq": 350,
        "koi_insol": 50,
        "koi_steff": 5800,
        "koi_slogg": 4.3,
        "koi_srad": 0.9
      }
    ],
    "hyperparams": {
      "candidate_threshold": 0.4,
      "confirmed_threshold": 0.7
    }
  }'
```

## K2 Mission Format
```bash
curl -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{
    "format": "k2",
    "data": [
      {
        "pl_orbper": 12.3,
        "pl_rade": 2.1,
        "pl_eqt": 450,
        "pl_insol": 95,
        "st_teff": 5600,
        "st_logg": 4.4,
        "st_rad": 1.1,
        "st_mass": 1.05,
        "st_met": 0.1
      }
    ],
    "hyperparams": {
      "candidate_threshold": 0.4,
      "confirmed_threshold": 0.7
    }
  }'
```

## TOI (TESS) Format
```bash
curl -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{
    "format": "toi",
    "data": [
      {
        "pl_orbper": 8.5,
        "pl_rade": 1.8,
        "pl_eqt": 400,
        "pl_insol": 80,
        "st_teff": 5700,
        "st_logg": 4.5,
        "st_rad": 0.95,
        "st_mass": 0.98,
        "st_met": -0.05
      }
    ],
    "hyperparams": {
      "candidate_threshold": 0.4,
      "confirmed_threshold": 0.7
    }
  }'
```

## Upload CSV File
```bash
curl -X POST http://localhost:8000/api/predict/csv/ \
  -F "file=@data/kepler.csv" \
  -F "format=kepler"
```

## Pretty Print JSON Response (with jq)
```bash
curl -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{
    "format": "kepler",
    "data": [
      {
        "koi_period": 10.5,
        "koi_prad": 2.5,
        "koi_teq": 500,
        "koi_insol": 100,
        "koi_steff": 5500,
        "koi_slogg": 4.5,
        "koi_srad": 1.0
      }
    ],
    "hyperparams": {
      "candidate_threshold": 0.4,
      "confirmed_threshold": 0.7
    }
  }' | jq .
```

## Custom Thresholds Example
Adjust classification thresholds to be more strict:
```bash
curl -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{
    "format": "kepler",
    "data": [
      {
        "koi_period": 10.5,
        "koi_prad": 2.5,
        "koi_teq": 500,
        "koi_insol": 100,
        "koi_steff": 5500,
        "koi_slogg": 4.5,
        "koi_srad": 1.0
      }
    ],
    "hyperparams": {
      "candidate_threshold": 0.6,
      "confirmed_threshold": 0.85
    }
  }'
```

## Hyperparameters
- **`candidate_threshold`** (0.0-1.0, default: 0.4): Minimum confidence for candidate classification
- **`confirmed_threshold`** (0.0-1.0, default: 0.7): Minimum confidence for confirmed classification

Classification logic:
- If confidence >= `confirmed_threshold` → Class 2 (Confirmed)
- Else if confidence >= `candidate_threshold` → Class 1 (Candidate)
- Else → Class 0 (False Positive)

## Prediction Classes
- **0**: False Positive
- **1**: Candidate
- **2**: Confirmed Planet

## Interactive Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
