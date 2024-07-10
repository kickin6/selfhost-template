#!/bin/bash

# Stop and remove existing containers
docker-compose down

# Remove orphaned volumes
docker volume prune -f

# Build and bring up the containers
docker-compose up --build

