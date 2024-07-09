#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to display help message
function display_help {
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  --coverage            Run tests with code coverage"
    echo "  --coverage --html     Run tests with code coverage and generate HTML report"
    echo "  --coverage --html --term   Run tests with code coverage, generate HTML report, and display results in the terminal"
    echo "  --clean               Delete the htmlcov directory before running tests"
    echo "  --help                Display this help message"
    echo
    exit 0
}

# Check for help flag
if [ "$1" == "--help" ]; then
    display_help
fi

# Check if coverage and clean flags are passed
COVERAGE=false
HTML_REPORT=false
TERM_REPORT=false
CLEAN=false
if [ "$1" == "--coverage" ]; then
  COVERAGE=true
  if [ "$2" == "--html" ]; then
    HTML_REPORT=true
    if [ "$3" == "--term" ]; then
      TERM_REPORT=true
    fi
  elif [ "$2" == "--term" ]; then
    TERM_REPORT=true
  fi
fi

if [ "$1" == "--clean" ] || [ "$2" == "--clean" ] || [ "$3" == "--clean" ]; then
  CLEAN=true
fi

# Clean the htmlcov directory if needed
if [ "$CLEAN" == true ]; then
  echo "Cleaning the htmlcov directory..."
  rm -rf htmlcov
fi

# Build and start the Docker Compose services in detached mode
echo "Starting Docker Compose services..."
docker-compose up --build -d

# Wait for a few seconds to ensure that all services are up and running
echo "Waiting for services to be fully started..."
sleep 2

# Run the tests inside the web container, optionally with code coverage
echo "Running tests inside the container..."
if [ "$COVERAGE" == true ]; then
  if [ "$HTML_REPORT" == true ] && [ "$TERM_REPORT" == true ]; then
    docker-compose exec web sh -c "PYTHONPATH=/app pytest -s -v --cov=/app --cov-report html --cov-report term"
    docker cp web:/app/htmlcov ./htmlcov
  elif [ "$HTML_REPORT" == true ]; then
    docker-compose exec web sh -c "PYTHONPATH=/app pytest -s -v --cov=/app --cov-report html"
    docker cp web:/app/htmlcov ./htmlcov
  elif [ "$TERM_REPORT" == true ]; then
    docker-compose exec web sh -c "PYTHONPATH=/app pytest -s -v --cov=/app --cov-report term"
  else
    docker-compose exec web sh -c "PYTHONPATH=/app pytest -s -v --cov=/app"
  fi
else
  docker-compose exec web sh -c "PYTHONPATH=/app pytest -s -v"
fi

# Capture the exit status of pytest
TEST_EXIT_CODE=$?

# Tear down the Docker Compose services
echo "Stopping Docker Compose services..."
docker-compose down

# Exit with the same status as pytest
exit $TEST_EXIT_CODE
