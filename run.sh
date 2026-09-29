#!/bin/bash
# Wrapper-Skript für Cron: aktiviert das venv und führt den Agenten aus.
cd "$(dirname "$0")"
source .venv/bin/activate
python main.py
