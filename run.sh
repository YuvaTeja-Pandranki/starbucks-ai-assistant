#!/bin/bash
echo "Starting Starbucks AI Assistant..."
conda run -n starbucks-ai python scripts/setup_vectorstore.py
conda run -n starbucks-ai uvicorn backend.main:app --reload --port 8000
