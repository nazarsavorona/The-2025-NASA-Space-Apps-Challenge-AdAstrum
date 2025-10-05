#!/bin/bash
# Test AdAstrum API using curl

echo "============================================================"
echo "Testing AdAstrum API with curl"
echo "============================================================"
echo ""

echo "[1/2] Testing Health Endpoint..."
echo ""
curl -X GET http://localhost:8000/
echo ""
echo ""

echo "[2/2] Testing Prediction Endpoint..."
echo ""
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
echo ""
echo ""

echo "============================================================"
echo "Test with multiple data points:"
echo "============================================================"
echo ""
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
      },
      {
        "koi_period": 365,
        "koi_prad": 1.0,
        "koi_teq": 288,
        "koi_insol": 1.0,
        "koi_steff": 5778,
        "koi_slogg": 4.4,
        "koi_srad": 1.0
      }
    ],
    "hyperparams": {
      "candidate_threshold": 0.4,
      "confirmed_threshold": 0.7
    }
  }'
echo ""
echo ""

echo "============================================================"
echo "API Documentation: http://localhost:8000/docs"
echo "============================================================"
