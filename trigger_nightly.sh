#!/bin/bash
# Trigger the nightly loop
cd /home/hunter/.openclaw/workspace/Personal-OS-Interface/api
source .venv/bin/activate
source .env
curl -s -X POST http://localhost:8000/api/monitoring/nightly/trigger
