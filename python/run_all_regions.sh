#!/bin/bash
# Corre el pipeline completo (2020-2025) para las 4 regiones, una a la vez.
set -uo pipefail

cd "$(dirname "$0")"
PY="../.venv/Scripts/python.exe"
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

REGIONS="santander quindio cordoba boyaca"

for region in $REGIONS; do
  echo "=========================================="
  echo "REGION: $region  ($(date))"
  echo "=========================================="
  "$PY" run_pipeline.py --region "$region" --fecha-inicio 2020-01-01 --fecha-fin 2025-12-31 \
    > "$LOG_DIR/pipeline_${region}.log" 2>&1
  status=$?
  echo "region=$region status=$status"
  if [ $status -ne 0 ]; then
    echo "FALLO en region $region, revisar $LOG_DIR/pipeline_${region}.log"
  fi
done

echo "=========================================="
echo "TODAS LAS REGIONES PROCESADAS ($(date))"
echo "=========================================="
