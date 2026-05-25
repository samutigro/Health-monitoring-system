#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-demo-secret-key}"

echo "GET /v1/health"
curl -sS "$BASE_URL/v1/health"
echo

echo "POST /v1/patients"
PATIENT_JSON="$(
  curl -sS -X POST "$BASE_URL/v1/patients" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{
      "name": "Mario Rossi",
      "age": 45,
      "weight": 78.5,
      "profile_picture": "https://example.com/images/patient-1.png"
    }'
)"
echo "$PATIENT_JSON"
PATIENT_ID="$(printf '%s' "$PATIENT_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
echo

echo "GET /v1/patients"
curl -sS "$BASE_URL/v1/patients?limit=100&offset=0" \
  -H "X-API-Key: $API_KEY"
echo

echo "GET /v1/patients/{patient_id}"
curl -sS "$BASE_URL/v1/patients/$PATIENT_ID" \
  -H "X-API-Key: $API_KEY"
echo

echo "PUT /v1/patients/{patient_id}"
curl -sS -X PUT "$BASE_URL/v1/patients/$PATIENT_ID" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "name": "Mario Rossi",
    "age": 46,
    "weight": 79.2,
    "profile_picture": "https://example.com/images/patient-1.png"
  }'
echo

echo "POST /v1/patients/{patient_id}/metrics/temperature"
curl -sS -X POST "$BASE_URL/v1/patients/$PATIENT_ID/metrics/temperature" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "timestamp": "2025-08-01T10:30:00Z",
    "value": 36.7
  }'
echo

echo "GET /v1/patients/{patient_id}/metrics/temperature"
curl -sS "$BASE_URL/v1/patients/$PATIENT_ID/metrics/temperature?start_time=2025-08-01T10:00:00Z&end_time=2025-08-01T11:00:00Z&limit=100&offset=0" \
  -H "X-API-Key: $API_KEY"
echo

echo "POST /v1/patients/{patient_id}/metrics/heart-rate"
python3 -c 'import json; print(json.dumps({"start_timestamp":"2025-08-01T10:00:00Z","samples":[72.0] * 600}))' |
curl -sS -X POST "$BASE_URL/v1/patients/$PATIENT_ID/metrics/heart-rate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d @-
echo

echo "GET /v1/patients/{patient_id}/metrics/heart-rate"
curl -sS "$BASE_URL/v1/patients/$PATIENT_ID/metrics/heart-rate?start_time=2025-08-01T10:00:00Z&end_time=2025-08-01T10:01:00Z&limit=10&offset=0" \
  -H "X-API-Key: $API_KEY"
echo
