"""
Final coverage tests for flask_app.py to achieve 100% coverage
Specifically targets lines 72 and 239
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# pylint: disable=import-error
# pylint: disable=wrong-import-position
from flask_app import create_app, scraping_status
# pylint: enable=wrong-import-position
# pylint: enable=import-error


@pytest.mark.web
def test_create_app_with_default_config():
    """Test app creation with default config (covers line 72)"""
    # Clear DATABASE_URL if it exists
    with patch.dict(os.environ, {}, clear=True):
        # Don't provide db_config or DATABASE_URL
        app = create_app()

        # Should use DEFAULT_DB_CONFIG
        assert app.db_config["host"] == "localhost"
        assert app.db_config["port"] == 5432
        assert app.db_config["dbname"] == "gradcafe_db"
        assert app.db_config["user"] == "momo"
        assert app.db_config["password"] == ""


@pytest.mark.integration
def test_load_new_data_with_successful_connection():
    """Test load_new_data_to_database with successful connections (covers line 239)"""
    app = create_app()

    with app.test_client() as client:
        scraping_status["is_running"] = False

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

            with patch("builtins.open", create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                with patch("load_data.GradCafeDataLoader") as mock_loader_class:
                    mock_loader = mock_loader_class.return_value
                    mock_loader.connect_to_database.return_value = True
                    mock_loader.load_data_from_jsonl.return_value = True
                    mock_loader.close_connection.return_value = None

                    # Mock psycopg connection for counting - need two successful connections
                    with patch("psycopg.connect") as mock_connect:
                        # Create two mock connections for the two get_db_connection() calls
                        mock_conn1 = Mock()
                        mock_cursor1 = Mock()
                        mock_cursor1.fetchone.return_value = (100,)  # Initial count
                        mock_cursor1.execute = Mock()
                        mock_conn1.cursor.return_value = mock_cursor1
                        mock_conn1.close = Mock()  # This will be called on line 227

                        mock_conn2 = Mock()
                        mock_cursor2 = Mock()
                        mock_cursor2.fetchone.return_value = (110,)  # Final count
                        mock_cursor2.execute = Mock()
                        mock_conn2.cursor.return_value = mock_cursor2
                        mock_conn2.close = Mock()  # This will be called on line 239

                        # Return different connections for each call
                        mock_connect.side_effect = [mock_conn1, mock_conn2]

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

                            # Verify both connections were closed
                            mock_conn1.close.assert_called_once()  # Line 227
                            mock_conn2.close.assert_called_once()  # Line 239

                            # Check success status
                            assert scraping_status["error"] is None
                            assert "Complete! Added 10 new records" in scraping_status["progress"]
