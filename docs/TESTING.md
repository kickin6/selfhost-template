### `docs/TESTING.md`

# Testing

## Running Tests

To run tests, you can use the `run_tests.sh` script. This script builds and starts the Docker Compose services, runs the tests inside the `web` container, and then tears down the services.

### Without Code Coverage

```bash
./run_tests.sh
```

### With Code Coverage

```bash
./run_tests.sh --coverage
```

### With Code Coverage and HTML Report

```bash
./run_tests.sh --coverage --html
```

### Cleaning the Coverage Directory Before Running Tests

If you want to delete the `htmlcov` directory before running the tests to ensure a clean state, use the `--clean` option:

```bash
./run_tests.sh --coverage --html --clean
```

## Test Coverage

If you ran the tests with code coverage and generated an HTML report, you can find the report in the `htmlcov` directory. To view the report, open the `index.html` file in a web browser.

To copy the coverage report from the container to your host machine:

```bash
docker cp web:/app/htmlcov ./htmlcov
```

Then open `htmlcov/index.html` in your web browser to view the coverage report.
