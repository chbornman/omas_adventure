#!/bin/bash

echo "Stopping containers..."
docker compose down

echo "Building containers..."
docker compose build --no-cache

echo "Starting containers in detached mode..."
docker compose up -d

echo "Following logs..."
docker compose logs -f