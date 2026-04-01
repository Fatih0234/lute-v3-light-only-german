#!/bin/bash
# Quick launcher for Lute v3
PORT="${1:-5001}"
source venv/bin/activate
python devstart.py --port "$PORT"
