#!/bin/bash
# Activate conda environment
source activate openvoice
# Install libmagic
conda install --yes libmagic
# Start the server
uvicorn openvoice_server:app --host "0.0.0.0" --port 8000 &
# Get its PID
PID=$!
# Wait for 60 seconds
sleep 60
# Kill the process
kill $PID
