#!/bin/bash
cd backend
source venv/bin/activate
echo "Starting Coursework Management System on http://localhost:3000"
uvicorn main:app --reload --port 3000 --host 0.0.0.0
