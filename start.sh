#!/bin/bash

# Kill any existing processes that might be holding onto our ports
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:8080 | xargs kill -9 2>/dev/null

echo "Starting Smarfa All-in-One..."

# Use concurrently to run all three services in one terminal window with color-coded logs
npx --yes concurrently \
  -n "PYTHON,GO" -c "blue,green" \
  "cd ai-service && ../.venv/bin/uvicorn app.service:app --host 0.0.0.0 --port 8001" \
  "cd gateway && go run cmd/main.go"
