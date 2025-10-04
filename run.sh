#!/usr/bin/env bash
set -e
uvicorn src.app.main:app --reload --port 8080