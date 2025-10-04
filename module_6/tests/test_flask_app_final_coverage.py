"""
Final tests to achieve 100% coverage for flask_app.py
Targets the remaining uncovered lines
"""

import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import after adding to path
# pylint: disable=import-error
# pylint: disable=wrong-import-position
from flask_app import create_app, scraping_status
# pylint: enable=wrong-import-position
# pylint: enable=import-error


class TestFlaskAppFinalCoverage:
    """Final tests to achieve 100% coverage for flask_app.py"""

    @pytest.mark.buttons
    def test_pull_data_when_busy(self):
        """Test pull-data endpoint when already running - covers line 252"""
        app = create_app()

        with app.test_client() as client:
            # Set status to running
            scraping_status["is_running"] = True

            response = client.post("/pull-data")
            assert response.status_code == 409
            data = response.get_json()
            assert data["busy"] is True

    @pytest.mark.buttons
    def test_update_analysis_when_busy(self):
        """Test update-analysis endpoint when busy - covers lines 266-267"""
        app = create_app()

        with app.test_client() as client:
            # Set status to running
            scraping_status["is_running"] = True

            response = client.post("/update-analysis")
            assert response.status_code == 409
            data = response.get_json()
            assert data["busy"] is True

    @pytest.mark.buttons
    def test_update_analysis_when_not_busy(self):
        """Test update-analysis endpoint when not busy - covers lines 268-269"""
        app = create_app()

        with app.test_client() as client:
            # Set status to not running
            scraping_status["is_running"] = False

            response = client.post("/update-analysis")
            assert response.status_code == 200
            data = response.get_json()
            assert data["ok"] is True

    @pytest.mark.web
    def test_get_status_endpoint(self):
        """Test status endpoint - covers line 274"""
        app = create_app()

        with app.test_client() as client:
            # Set some status values
            scraping_status["is_running"] = False
            scraping_status["progress"] = "Test progress"
            scraping_status["error"] = None
            scraping_status["last_update"] = None

            response = client.get("/status")
            assert response.status_code == 200
            data = response.get_json()
            assert data["is_running"] is False
            assert data["progress"] == "Test progress"
            assert data["error"] is None

    @pytest.mark.integration
    def test_run_data_pipeline_with_injected_scraper(self):
        """Test data pipeline with injected scraper - covers lines 84-93"""
        # Create a mock scraper
        mock_scraper = Mock()
        mock_scraper.scrape.return_value = "Test data scraped"

        app = create_app(scraper=mock_scraper)

        with app.test_client() as client:
            # Reset status
            scraping_status["is_running"] = False
            scraping_status["error"] = None

            with patch("threading.Thread") as mock_thread_class:
                # Make thread execution synchronous
                def mock_init(target=None, **kwargs):  # pylint: disable=unused-argument
                    mock_thread = Mock()
                    mock_thread.target = target
                    mock_thread.daemon = True

                    def mock_start():
                        target()

                    mock_thread.start = mock_start
                    return mock_thread

                mock_thread_class.side_effect = mock_init

                response = client.post("/pull-data")
                assert response.status_code == 202

                # Verify scraper was called
                mock_scraper.scrape.assert_called_once()

                # Check status was updated
                assert scraping_status["progress"] == "Complete! Test data loaded"
                assert scraping_status["is_running"] is False
                assert scraping_status["last_update"] is not None

    @pytest.mark.integration
    def test_run_data_pipeline_with_injected_scraper_exception(self):
        """Test data pipeline when injected scraper raises exception - covers lines 84-93 error path"""  # pylint: disable=line-too-long
        # Create a mock scraper that raises an exception
        mock_scraper = Mock()
        mock_scraper.scrape.side_effect = RuntimeError("Scraper failed")

        app = create_app(scraper=mock_scraper)

        with app.test_client() as client:
            # Reset status
            scraping_status["is_running"] = False
            scraping_status["error"] = None

            with patch("threading.Thread") as mock_thread_class:

                def mock_init(target=None, **kwargs):  # pylint: disable=unused-argument
                    mock_thread = Mock()
                    mock_thread.target = target
                    mock_thread.daemon = True

                    def mock_start():
                        target()

                    mock_thread.start = mock_start
                    return mock_thread

                mock_thread_class.side_effect = mock_init

                response = client.post("/pull-data")
                assert response.status_code == 202

                # Verify scraper was called
                mock_scraper.scrape.assert_called_once()

                # Check error was captured (either in error field or progress field)
                error_captured = scraping_status["error"] is not None or "Error:" in scraping_status.get("progress", "")  # pylint: disable=line-too-long
                assert error_captured
                if scraping_status["error"]:
                    assert "Scraper failed" in scraping_status["error"]
                else:
                    assert "Error:" in scraping_status["progress"]
                assert scraping_status["is_running"] is False

    @pytest.mark.web
    def test_database_url_parsing_edge_case(self):
        """Test DATABASE_URL parsing with edge cases - covers line 40"""
        # Test with a URL that has all components
        test_url = "postgresql://user:pass@host:5432/dbname"

        with patch.dict(os.environ, {"DATABASE_URL": test_url}, clear=True):
            # Remove any existing DATABASE_URL to ensure clean state
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
            os.environ["DATABASE_URL"] = test_url

            app = create_app()

            assert app.db_config["host"] == "host"
            assert app.db_config["port"] == 5432
            assert app.db_config["dbname"] == "dbname"
            assert app.db_config["user"] == "user"
            assert app.db_config["password"] == "pass"

    @pytest.mark.db
    def test_get_db_connection_success_direct(self):
        """Direct test for get_db_connection success - targets lines 67-69"""
        # We need to test the actual execution of get_db_connection
        # Let's create an app and directly call the function

        with patch("flask_app.psycopg") as mock_psycopg:
            # Create a successful connection mock
            mock_conn = Mock()
            mock_conn.cursor = Mock()
            mock_conn.close = Mock()
            mock_psycopg.connect.return_value = mock_conn

            # Create app
            app = create_app()

            # Now we need to trigger get_db_connection through a route
            # The index route calls it
            with app.test_client() as client:
                with patch("flask_app.GradCafeQueryAnalyzer") as mock_analyzer_class:
                    mock_analyzer = mock_analyzer_class.return_value
                    mock_analyzer.connect_to_database.return_value = True
                    mock_analyzer.run_all_queries.return_value = None
                    mock_analyzer.results = {}
                    mock_analyzer.close_connection.return_value = None

                    # Set up cursor mock for the queries in index route
                    mock_cursor = Mock()
                    mock_cursor.fetchone.side_effect = [(100,), (datetime.now(),)]
                    mock_cursor.execute = Mock()
                    mock_conn.cursor.return_value = mock_cursor

                    # Make the request
                    response = client.get("/")

                    # Should be successful
                    assert response.status_code == 200

                    # Verify connection was made
                    mock_psycopg.connect.assert_called()
                    assert mock_conn.cursor.called
                    assert mock_conn.close.called

    @pytest.mark.integration
    def test_complete_data_pipeline_with_db_success(self):
        """Test complete pipeline including successful database operations - ensures lines 67-69 are covered"""  # pylint: disable=line-too-long
        with patch("flask_app.psycopg") as mock_psycopg:
            # Create mock connection
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchone.side_effect = [(100,), (110,)]  # For counting records
            mock_cursor.execute = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.close = Mock()
            mock_psycopg.connect.return_value = mock_conn

            app = create_app()

            with app.test_client() as client:
                scraping_status["is_running"] = False

                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

                    with patch("builtins.open", create=True) as mock_open:
                        mock_open.return_value.__enter__ = Mock()
                        mock_open.return_value.__exit__ = Mock(return_value=None)
                        mock_open.return_value.write = Mock()

                        # Import and patch at the correct location
                        with patch("load_data.GradCafeDataLoader") as mock_loader_class:
                            mock_loader = mock_loader_class.return_value
                            mock_loader.connect_to_database.return_value = True
                            mock_loader.load_data_from_jsonl.return_value = True
                            mock_loader.close_connection.return_value = None

                            with patch("threading.Thread") as mock_thread_class:

                                def mock_init(target=None, **kwargs):  # pylint: disable=unused-argument
                                    mock_thread = Mock()
                                    mock_thread.target = target
                                    mock_thread.daemon = True

                                    def mock_start():
                                        target()

                                    mock_thread.start = mock_start
                                    return mock_thread

                                mock_thread_class.side_effect = mock_init

                                response = client.post("/pull-data")
                                assert response.status_code == 202

                                # Verify database connection was made successfully
                                mock_psycopg.connect.assert_called()
                                assert mock_conn.cursor.called
                                assert mock_conn.close.called

                                # Check success
                                assert scraping_status["error"] is None
                                assert (
                                    "Complete! Added 10 new records" in scraping_status["progress"]
                                )

    @pytest.mark.web
    def test_create_app_with_config_and_db_url(self):
        """Test app creation with both config and DATABASE_URL - covers line 40"""
        # Set DATABASE_URL
        test_url = "postgresql://dbuser:dbpass@dbhost:5433/mydb"

        # Create config that should be overridden by DATABASE_URL
        test_config = {"DEBUG": True}

        with patch.dict(os.environ, {"DATABASE_URL": test_url}):
            # Create app with config - DATABASE_URL should take precedence for db_config
            app = create_app(config=test_config)

            # Config should be applied
            assert app.config.get("DEBUG") is True

            # DATABASE_URL should be parsed for db_config
            assert app.db_config["host"] == "dbhost"
            assert app.db_config["port"] == 5433
            assert app.db_config["dbname"] == "mydb"
            assert app.db_config["user"] == "dbuser"
            assert app.db_config["password"] == "dbpass"
