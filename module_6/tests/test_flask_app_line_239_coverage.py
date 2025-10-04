"""
Specific test to cover line 239 in flask_app.py
Line 239: raise RuntimeError("Failed to load new data")
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# pylint: disable=import-error,wrong-import-position
from flask_app import create_app, scraping_status
# pylint: enable=import-error,wrong-import-position


@pytest.mark.integration
def test_load_new_data_failure_raises_exception():
    """Test that line 239 (raise Exception) is executed when load_data_from_jsonl fails"""

    app = create_app()

    # Access the load_new_data_to_database function from the app context
    with app.app_context():
        # We need to call load_new_data_to_database directly
        # First, let's get the function from the closure

        # Mock the GradCafeDataLoader
        with patch("load_data.GradCafeDataLoader") as mock_loader_class:
            mock_loader = mock_loader_class.return_value
            mock_loader.connect_to_database.return_value = True

            # Mock successful first connection for initial count
            with patch("psycopg.connect") as mock_connect:
                mock_conn = Mock()
                mock_cursor = Mock()
                mock_cursor.fetchone.return_value = (100,)
                mock_cursor.execute = Mock()
                mock_conn.cursor.return_value = mock_cursor
                mock_conn.close = Mock()
                mock_connect.return_value = mock_conn

                # Make load_data_from_jsonl return False to trigger the exception
                mock_loader.load_data_from_jsonl.return_value = False

                # Import and call the function directly
                # This is a bit tricky since it's defined inside create_app
                # We'll trigger it through the pipeline

                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

                    with patch("builtins.open", create=True) as mock_open:
                        mock_file = MagicMock()
                        mock_open.return_value.__enter__.return_value = mock_file

                        with patch("threading.Thread") as mock_thread_class:
                            # Store the target function
                            target_func = None

                            def mock_init(target=None, **kwargs):  # pylint: disable=unused-argument
                                nonlocal target_func
                                target_func = target
                                mock_thread = Mock()
                                mock_thread.target = target
                                mock_thread.daemon = True

                                def mock_start():
                                    # Execute the target function
                                    target()

                                mock_thread.start = mock_start
                                return mock_thread

                            mock_thread_class.side_effect = mock_init

                            # Trigger the pipeline
                            with app.test_client() as client:
                                response = client.post("/pull-data")
                                assert response.status_code == 202

                                # The error should be captured
                                assert scraping_status["error"] is not None
                                # Check for specific or generic database error
                                error_msg = scraping_status["error"]
                                assert (
                                    "Failed to load new data" in error_msg
                                    or "Database loading error" in error_msg
                                )


@pytest.mark.db
def test_direct_load_failure_exception():
    """Direct test of the exception on line 239"""
    app = create_app()

    # We need to test the load_new_data_to_database function
    # Since it's defined inside create_app, we need to be creative

    # Create a test that directly exercises the code path
    with app.test_client() as client:
        # Patch everything needed for the data pipeline
        with patch("subprocess.run") as mock_run:
            # Make all subprocess calls succeed
            mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

            with patch("builtins.open", create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                # This is the key: patch load_data module
                with patch("load_data.GradCafeDataLoader") as mock_loader_class:
                    mock_loader = mock_loader_class.return_value
                    mock_loader.connect_to_database.return_value = True

                    # First get_db_connection for initial count succeeds
                    with patch("psycopg.connect") as mock_connect:
                        mock_conn = Mock()
                        mock_cursor = Mock()
                        mock_cursor.fetchone.return_value = (100,)
                        mock_cursor.execute = Mock()
                        mock_conn.cursor.return_value = mock_cursor
                        mock_conn.close = Mock()
                        mock_connect.return_value = mock_conn

                        # THIS IS THE KEY: Make load_data_from_jsonl return False
                        # This will trigger line 239: raise RuntimeError("Failed to load new data")
                        mock_loader.load_data_from_jsonl.return_value = False

                        # Execute synchronously
                        scraping_status["is_running"] = False

                        with patch("threading.Thread") as mock_thread_class:

                            def mock_init(target=None, **kwargs):  # pylint: disable=unused-argument
                                mock_thread = Mock()
                                mock_thread.target = target
                                mock_thread.daemon = True

                                def mock_start():
                                    # Execute immediately
                                    target()

                                mock_thread.start = mock_start
                                return mock_thread

                            mock_thread_class.side_effect = mock_init

                            # Make the request
                            response = client.post("/pull-data")
                            assert response.status_code == 202

                            # Verify the exception was raised and caught
                            assert scraping_status["error"] is not None
                            # Check for specific exception or wrapper message
                            error_msg = scraping_status["error"]
                            assert (
                                "Failed to load new data" in error_msg
                                or "Database loading error" in error_msg
                            )
