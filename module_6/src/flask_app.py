#!/usr/bin/env python3
"""
Flask Web Application for Grad Café Data Analysis.

Displays query results and provides data update functionality.
"""

import os
import subprocess
import threading
from datetime import datetime

import psycopg
from psycopg import sql
from flask import Flask, jsonify, render_template

# Import our query analyzer and config
# pylint: disable=import-error
from config import DB_CONFIG
from query_data import GradCafeQueryAnalyzer
# pylint: enable=import-error

# Global variables for tracking operations
scraping_status = {
    "is_running": False,
    "progress": "",
    "last_update": None,
    "error": None,
}


def setup_db_config(flask_app, db_config):
    """
    Set up database configuration for the Flask app.
    
    :param flask_app: Flask application instance
    :param db_config: Database configuration dictionary or None
    """
    if db_config:
        flask_app.db_config = db_config
    elif os.getenv("DATABASE_URL"):
        # Parse DATABASE_URL for testing
        # pylint: disable=import-outside-toplevel
        import urllib.parse
        # pylint: enable=import-outside-toplevel

        url = urllib.parse.urlparse(os.getenv("DATABASE_URL"))
        flask_app.db_config = {
            "host": url.hostname,
            "port": url.port or 5432,
            "dbname": url.path[1:],  # Remove leading slash
            "user": url.username,
            "password": url.password or "",
        }
    else:
        flask_app.db_config = DB_CONFIG.copy()


def create_app(config=None, db_config=None, scraper=None):
    # pylint: disable=too-many-locals,too-many-statements
    """
    Application factory function.

    Creates and configures the Flask application, sets up database configuration,
    and registers routes. Supports dependency injection of a scraper for testing.

    :param config: Flask configuration dictionary to apply to the app.
    :type config: dict | None
    :param db_config: Database connection config (host, port, dbname, user, password).
                      If not provided, uses ``DATABASE_URL`` or DEFAULT_DB_CONFIG.
    :type db_config: dict | None
    :param scraper: Optional scraper object with a ``scrape()`` method (for tests).
    :type scraper: object | None
    :return: Configured Flask application instance.
    :rtype: Flask
    """
    flask_app = Flask(__name__)

    # Apply configuration
    if config:
        flask_app.config.update(config)

    # Set up database configuration
    setup_db_config(flask_app, db_config)

    # Set up scraper (for dependency injection in tests)
    flask_app.scraper = scraper  # pylint: disable=assigning-non-slot

    def get_db_connection():
        """
        Create a new database connection using app configuration.

        :return: A new psycopg connection object or None on error.
        :rtype: psycopg.Connection | None
        """
        try:
            conn = psycopg.connect(**flask_app.db_config)  # pylint: disable=no-member
            return conn
        except psycopg.Error as exc:
            print(f"Database connection error: {exc}")
            return None

    def run_scraper_step(base_dir):
        """Run the incremental scraper step."""
        scraping_status["progress"] = "Step 1/4: Scraping new data..."
        print("[DEBUG] Running incremental_scraper.py...")

        result = subprocess.run(
            ["python", "incremental_scraper.py"],
            capture_output=True,
            text=True,
            cwd=base_dir,
            check=False,
        )

        print(f"[DEBUG] Scraper return code: {result.returncode}")
        print(f"[DEBUG] Scraper stdout: {result.stdout}")
        if result.stderr:
            print(f"[DEBUG] Scraper stderr: {result.stderr}")

        if result.returncode != 0:
            raise RuntimeError(f"Scraping failed: {result.stderr}")

        return result

    def run_cleaner_step(base_dir):
        """Run the data cleaning step."""
        scraping_status["progress"] = "Step 2/4: Cleaning new data..."
        print("[DEBUG] Running clean.py...")

        result = subprocess.run(
            [
                "python",
                "clean.py",
                "--input",
                "new_applicant_data.json",
                "--output",
                "new_cleaned_applicant_data.json",
            ],
            capture_output=True,
            text=True,
            cwd=base_dir,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Cleaning failed: {result.stderr}")

        return result

    def run_llm_step(base_dir):
        """Run the LLM standardization step."""
        scraping_status["progress"] = "Step 3/4: LLM standardization..."
        print("[DEBUG] Running LLM standardization...")

        llm_dir = os.path.join(base_dir, "llm_hosting")
        result = subprocess.run(
            [
                "python",
                "app.py",
                "--file",
                "../new_cleaned_applicant_data.json",
                "--stdout",
            ],
            capture_output=True,
            text=True,
            cwd=llm_dir,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(f"LLM processing failed: {result.stderr}")

        # Save LLM output
        llm_output_path = os.path.join(base_dir, "new_llm_extend_applicant_data.jsonl")
        with open(llm_output_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)

        return llm_output_path

    def handle_test_scraper():
        """Handle test scraper execution."""
        print("[DEBUG] Using injected scraper")
        try:
            result = flask_app.scraper.scrape()
            print(f"[DEBUG] Scraper completed: {result}")
            scraping_status["progress"] = "Complete! Test data loaded"
            scraping_status["last_update"] = datetime.now()
        except (AttributeError, RuntimeError) as exc:
            print(f"[DEBUG] Scraper failed with exception: {exc}")
            raise exc

    def process_pipeline_steps(base_dir):
        """Process the main pipeline steps."""
        # Step 1: Incremental scraping
        result = run_scraper_step(base_dir)

        # Check if new data was found
        if "No new data found" in result.stdout or "No new data" in result.stdout:
            scraping_status["progress"] = "No new data available"
            scraping_status["is_running"] = False
            scraping_status["last_update"] = datetime.now()
            print("[DEBUG] No new data found, ending pipeline")
            return None

        # Step 2: Clean new data
        run_cleaner_step(base_dir)

        # Step 3: LLM standardization
        llm_output_path = run_llm_step(base_dir)

        # Step 4: Load new data into database
        scraping_status["progress"] = "Step 4/4: Loading new data into database..."
        print("[DEBUG] Loading data to database...")

        new_count = load_new_data_to_database(llm_output_path)

        scraping_status["progress"] = f"Complete! Added {new_count} new records"
        scraping_status["last_update"] = datetime.now()
        print(f"[DEBUG] Pipeline complete! Added {new_count} new records")

        return new_count

    def run_data_pipeline():
        """
        Run the complete data pipeline (scrape → clean → LLM → load).

        Updates the global ``scraping_status`` with progress, errors, and completion time.
        """
        print(f"[DEBUG] Starting data pipeline in thread {threading.current_thread().name}")

        try:
            scraping_status["is_running"] = True
            scraping_status["error"] = None
            scraping_status["progress"] = "Starting data pipeline..."

            # Use injected scraper if available (for testing)
            if flask_app.scraper:
                handle_test_scraper()
                return

            base_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"[DEBUG] Base directory: {base_dir}")

            process_pipeline_steps(base_dir)

        except (RuntimeError, IOError, subprocess.SubprocessError) as exc:
            print(f"[DEBUG] Pipeline error: {str(exc)}")
            # pylint: disable=import-outside-toplevel
            import traceback
            # pylint: enable=import-outside-toplevel

            traceback.print_exc()
            scraping_status["error"] = str(exc)
            scraping_status["progress"] = f"Error: {str(exc)}"

        finally:
            scraping_status["is_running"] = False
            print("[DEBUG] Data pipeline thread finished")

    def load_new_data_to_database(filename: str) -> int:
        """
        Load new data from a JSONL file into the database.

        Uses :class:`load_data.GradCafeDataLoader` to load rows and computes the
        number of newly added records by comparing counts before/after.

        :param filename: Path to the JSONL file produced by the LLM step.
        :type filename: str
        :return: Number of new rows added to ``applicant_data``.
        :rtype: int
        :raises Exception: If database connection or loading fails.
        """
        try:
            # Import the data loader functionality
            # pylint: disable=import-outside-toplevel,import-error
            from load_data import GradCafeDataLoader
            # pylint: enable=import-outside-toplevel,import-error

            loader = GradCafeDataLoader(flask_app.db_config)  # pylint: disable=no-member
            if not loader.connect_to_database():
                raise RuntimeError("Failed to connect to database")

            # Count existing records
            conn = get_db_connection()
            # pylint: disable=no-member
            cursor = conn.cursor()
            # Compose SQL query with identifier and limit
            count_query = sql.SQL("SELECT COUNT(*) FROM {table} LIMIT {limit}").format(
                table=sql.Identifier('applicant_data'),
                limit=sql.Literal(1)
            )
            cursor.execute(count_query)
            initial_count = cursor.fetchone()[0]
            conn.close()
            # pylint: enable=no-member

            # Load new data
            success = loader.load_data_from_jsonl(filename)
            if not success:
                raise RuntimeError("Failed to load new data")

            # Count final records
            conn = get_db_connection()
            # pylint: disable=no-member
            cursor = conn.cursor()
            # Reuse the same count query
            cursor.execute(count_query)
            final_count = cursor.fetchone()[0]
            conn.close()
            # pylint: enable=no-member

            loader.close_connection()

            return final_count - initial_count

        except (RuntimeError, psycopg.Error) as exc:
            raise RuntimeError(f"Database loading error: {exc}") from exc

    def get_analysis_results():
        """Get analysis results from the database."""
        analyzer = GradCafeQueryAnalyzer(flask_app.db_config)  # pylint: disable=no-member
        if not analyzer.connect_to_database():
            return None, "Failed to connect to database"

        analyzer.run_all_queries()
        results = analyzer.results
        analyzer.close_connection()
        return results, None

    def get_database_stats():
        """Get database statistics."""
        conn = get_db_connection()
        if conn:
            # pylint: disable=no-member
            cursor = conn.cursor()
            # Compose count query
            count_query = sql.SQL("SELECT COUNT(*) FROM {table} LIMIT {limit}").format(
                table=sql.Identifier('applicant_data'),
                limit=sql.Literal(1)
            )
            cursor.execute(count_query)
            total_records = cursor.fetchone()[0]

            # Compose max date query
            max_date_query = sql.SQL("SELECT MAX({date_column}) FROM {table} LIMIT {limit}").format(
                date_column=sql.Identifier('date_added'),
                table=sql.Identifier('applicant_data'),
                limit=sql.Literal(1)
            )
            cursor.execute(max_date_query)
            latest_date = cursor.fetchone()[0]
            conn.close()
            # pylint: enable=no-member
            return total_records, latest_date
        return 0, None

    @flask_app.route("/")
    @flask_app.route("/analysis")
    def index():
        """
        Render the main analysis page.

        Connects to the database, executes analysis queries via
        :class:`query_data.GradCafeQueryAnalyzer`, fetches basic DB stats, and
        renders the ``index.html`` template with results.

        :return: Rendered HTML for the analysis page.
        :rtype: str
        """
        try:
            # Get all query results
            results, error = get_analysis_results()
            if error:
                return render_template("error.html", error=error)

            # Get database stats
            total_records, latest_date = get_database_stats()

            return render_template(
                "index.html",
                results=results,
                total_records=total_records,
                latest_date=latest_date,
                scraping_status=scraping_status,
            )

        except (psycopg.Error, KeyError) as exc:
            return render_template("error.html", error=str(exc))

    @flask_app.route("/pull-data", methods=["POST"])
    def pull_data():
        """
        Trigger the background data pipeline (scrape → clean → LLM → load).

        If a pipeline is already running, responds with HTTP 409 and
        ``{"busy": true}``. Otherwise, starts a background thread and returns
        HTTP 202 with ``{"ok": true}``.

        :return: JSON status and HTTP status code.
        :rtype: flask.Response
        """

        if scraping_status["is_running"]:
            return jsonify({"busy": True}), 409

        # Start data pipeline in background thread
        thread = threading.Thread(target=run_data_pipeline)
        thread.daemon = True
        thread.start()

        return jsonify({"ok": True}), 202

    @flask_app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        """
        Refresh analysis results (fast path).

        If the data pipeline is currently running, responds with HTTP 409 and
        ``{"busy": true}``. Otherwise, returns 200 with ``{"ok": true}``.
        This endpoint is intended for lightweight refresh of cached analysis.

        :return: JSON status and HTTP status code.
        :rtype: flask.Response
        """

        if scraping_status["is_running"]:
            return jsonify({"busy": True}), 409

        return jsonify({"ok": True}), 200

    @flask_app.route("/status")
    def get_status():
        """
        Return current scraping status as JSON.

        :return: Dictionary with keys: ``is_running``, ``progress``,
                 ``last_update``, ``error``.
        :rtype: flask.Response
        """
        return jsonify(scraping_status)

    @flask_app.errorhandler(404)
    def not_found(_error):
        """
        Handle 404 Not Found errors.

        :param _error: Flask error object (unused).
        :type _error: Exception
        :return: Rendered error page and HTTP 404.
        :rtype: tuple[str, int]
        """
        return render_template("error.html", error="Page not found"), 404

    @flask_app.errorhandler(500)
    def internal_error(_error):
        """
        Handle 500 Internal Server Error.

        :param _error: Flask error object (unused).
        :type _error: Exception
        :return: Rendered error page and HTTP 500.
        :rtype: tuple[str, int]
        """
        return render_template("error.html", error="Internal server error"), 500

    return flask_app
    # pylint: enable=too-many-locals,too-many-statements


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=True)
