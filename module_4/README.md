# Module 4 - Pytest and Sphinx Documentation

**JHU EP 605.256 – Modern Software Concepts in Python**

This module implements a comprehensive pytest testing suite for the Flask application from Module 3, following Test-Driven Development (TDD) principles with 100% coverage requirements, and includes complete Sphinx documentation.

## Assignment Documentation & Deliverables

- ** Complete Sphinx Documentation**: [Read the Docs](https://jhu-software-concepts-wl.readthedocs.io/en/latest/)
- ** Coverage Report**: `coverage_summary.txt` - 100% test coverage achieved (229/229 tests passing)
- ** GitHub Actions CI**: `GitHub_Action_CL_Screenshot.png` - Proof of successful automated testing
- ** Workflow Configuration**: `.github/workflows/tests.yml` - CI/CD pipeline setup

## Overview

Module 4 transforms the Module 3 Flask application into a fully testable, production-ready system that meets all assignment requirements:

### Core Features Implemented
- **Flask Factory Pattern**: Scalable app initialization with dependency injection via `create_app(...)`
- **Comprehensive Test Suite**: 229 tests across 5 categories with 100% pass rate
- **Mock Testing Infrastructure**: Isolated testing without external dependencies or network calls
- **API Compliance**: Proper HTTP status codes (200/202/409) and JSON responses
- **UI Testing**: Button interactions with stable selectors and HTML parsing via BeautifulSoup
- **100% Code Coverage**: All source modules achieve complete test coverage
- **Continuous Integration**: Automated testing via GitHub Actions with PostgreSQL
- **Complete Documentation**: Sphinx-generated docs with API reference and testing guides

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL database (for production)
- SQLite (for testing)
- Required packages: `pytest`, `pytest-cov`, `flask`, `psycopg`, `beautifulsoup4`

### Installation

1. Install dependencies:
```bash
pip install -r src/requirements.txt
pip install pytest pytest-cov beautifulsoup4
```

2. Run the comprehensive test suite:
```bash
pytest tests/ -v
```

3. Run with markers (as required by assignment):
```bash
pytest -m "web or buttons or analysis or db or integration"
```

4. Run the application:
```bash
cd src && python flask_app.py
```

## Testing Framework

### Required Test Categories (Assignment Compliance)

The test suite implements all 5 required test categories with proper pytest markers:

#### 1. **Flask App & Page Rendering** - `test_flask_page.py`
- **Marker**: `@pytest.mark.web`
- **Tests**: App factory/config, GET /analysis (status 200), required buttons, "Analysis" and "Answer:" labels

#### 2. **Buttons & Busy-State Behavior** - `test_buttons.py`
- **Marker**: `@pytest.mark.buttons`
- **Tests**: POST /pull-data (200/409), POST /update-analysis (200/409), busy gating with `{"busy": true}`

#### 3. **Analysis Formatting** - `test_analysis_format.py`
- **Marker**: `@pytest.mark.analysis`
- **Tests**: "Answer:" labels, percentage formatting with exactly 2 decimals (regex validation)

#### 4. **Database Writes** - `test_db_insert.py`
- **Marker**: `@pytest.mark.db`
- **Tests**: Insert on pull, idempotency/constraints, query function with required Module-3 schema

#### 5. **Integration Tests** - `test_integration_end_to_end.py`
- **Marker**: `@pytest.mark.integration`
- **Tests**: End-to-end (pull → update → render), multiple pulls with uniqueness policy

### Additional Coverage Tests
- **Module-Specific Coverage**: `test_clean.py`, `test_load_data.py`, `test_query_data.py`, `test_scrape.py`, `test_incremental_scraper.py`
- **Flask Application Coverage**: Multiple test files ensuring 100% coverage of all code paths

### Running Tests

```bash
# Run entire suite (all tests must pass)
pytest tests/ -v

# Run all tests with required markers
pytest -m "web or buttons or analysis or db or integration"

# Run specific categories
pytest -m web          # Flask route/page tests
pytest -m buttons      # Button behavior and busy-state
pytest -m analysis     # Formatting/rounding of analysis output
pytest -m db          # Database schema/inserts/selects
pytest -m integration # End-to-end flows

# Run with coverage reporting
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=100
```

## Coverage Summary
*Required test coverage of 100% reached. Coverage data verified in `coverage_summary.txt`*

## File Structure

```
module_4/
├── src/                           # Application source code
│   ├── flask_app.py              # Main Flask app with factory pattern
│   ├── query_data.py             # Database query operations
│   ├── load_data.py              # Data loading utilities
│   ├── clean.py                  # Data cleaning operations
│   ├── scrape.py                 # Web scraping functionality
│   ├── incremental_scraper.py    # Incremental scraping operations
│   ├── requirements.txt          # Python dependencies
│   ├── templates/
│   │   ├── index.html            # Analysis page template
│   │   ├── base.html             # Base template
│   │   └── error.html            # Error page template
│   ├── static/
│   │   ├── css/style.css         # Application styles
│   │   └── js/main.js            # Client-side JavaScript
│   └── llm_hosting/              # LLM hosting components
├── tests/                        # Comprehensive test suite (229 tests)
│   ├── conftest.py               # Test fixtures and mock components
│   ├── test_flask_page.py        # Web functionality tests (@pytest.mark.web)
│   ├── test_buttons.py           # Button interaction tests (@pytest.mark.buttons)
│   ├── test_analysis_format.py   # Format verification tests (@pytest.mark.analysis)
│   ├── test_db_insert.py         # Database operation tests (@pytest.mark.db)
│   ├── test_integration_end_to_end.py # End-to-end tests (@pytest.mark.integration)
│   └── test_*.py                 # Additional coverage tests
├── docs/                         # Sphinx documentation
│   ├── source/                   # Documentation source files
│   │   ├── conf.py               # Sphinx configuration
│   │   ├── index.rst             # Main documentation index
│   │   ├── api.rst               # API documentation (autodoc)
│   │   ├── architecture.rst      # Architecture documentation
│   │   ├── installation.rst      # Installation guide
│   │   ├── testing.rst           # Testing documentation
│   │   └── usage.rst             # Usage documentation
│   └── build/html/               # Built HTML documentation
├── .github/workflows/            # GitHub Actions CI/CD
│   └── tests.yml                 # Automated testing workflow
├── htmlcov/                      # HTML coverage reports
├── pytest.ini                   # Pytest configuration with markers
├── .coveragerc                   # Coverage configuration
├── coverage_summary.txt          # Coverage proof (assignment deliverable)
├── GitHub_Action_CL_Screenshot.png # CI success proof (assignment deliverable)
└── README.md                     # This documentation
```

## Test Infrastructure (Assignment Compliance)
## GitHub Actions CI/CD

### Automated Testing Workflow
- **File**: `.github/workflows/tests.yml`
- **Features**: PostgreSQL service, automated pytest execution
- **Proof**: `GitHub_Action_CL_Screenshot.png` shows successful green run
- **Status**:  All tests pass in CI environment

## Sphinx Documentation

### Published Documentation
- **URL**: https://jhu-software-concepts-wl.readthedocs.io/en/latest/
- **Format**: HTML via Read the Docs integration
- **Content**: Complete developer documentation with API reference

## References

- **Assignment**: JHU EP 605.256 Module 4 - Pytest and Sphinx
- **Documentation**: https://jhu-software-concepts-wl.readthedocs.io/en/latest/
- **Module 3**: Base Flask application and database schema
- **Pytest Documentation**: Testing framework and fixtures
- **Flask Testing**: Test client and application factory patterns
- **BeautifulSoup**: HTML parsing and verification
- **PostgreSQL**: Database schema and operations
- **Sphinx**: Documentation generation and Read the Docs integration
