# Python Dependency Analysis for flask_app.py

## Dependencies Found

The `flask_app.py` file demonstrates a well-structured Flask web application with several key dependency categories. **Flask** serves as the core web framework, providing routing, templating, and HTTP response handling for the graduate school data analysis interface. **psycopg** acts as the PostgreSQL database adapter, enabling secure database connections and parameterized SQL queries to prevent injection attacks. The application imports three critical local modules: `config.py` for centralized database configuration management, `query_data.py` containing the `GradCafeQueryAnalyzer` class for executing analytical queries, and `load_data.py` with the `GradCafeDataLoader` class for data ingestion operations. **Standard library modules** including `os`, `subprocess`, `threading`, and `datetime` provide essential system integration capabilities, allowing the application to execute background data pipeline processes, manage concurrent operations, and handle file system interactions. The dependency graph reveals a clean separation of concerns where flask_app.py acts as the main orchestrator, coordinating between the web interface, database operations, and data processing components. This modular architecture ensures maintainability and allows for independent testing of each component while providing a unified web-based interface for the Grad Café data analysis system.

## Generated Files

- `dependency.svg` - Visual dependency graph showing module relationships
- `dependency_analysis.md` - This analysis document
