#!/bin/bash

# Koyeb startup script for Sales Engagement Platform

# Set default port if not provided
export PORT=${PORT:-8000}

# Start the application
echo "Starting Sales Engagement Platform on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1