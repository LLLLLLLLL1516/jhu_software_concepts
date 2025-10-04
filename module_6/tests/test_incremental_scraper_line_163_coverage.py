#!/usr/bin/env python3
"""
Test specifically to cover line 163 in incremental_scraper.py
Line 163: print(f"Progress: {len(new_results)} new entries found")
This line only executes when len(new_results) is a multiple of 50
"""

import os
import sys
from datetime import date
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.mark.integration
def test_scrape_with_50_results_for_progress_line():
    """Test that triggers the progress print statement at line 163"""
    # Mock database connection
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (date(2025, 8, 1),)  # Old date
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = None
    mock_conn.close = MagicMock()

    # Mock HTTP
    mock_http = MagicMock()
    mock_response = MagicMock()
    mock_response.data = b"<html><body>Test</body></html>"
    mock_response.status = 200
    mock_http.request.return_value = mock_response

    with patch("psycopg.connect", return_value=mock_conn):
        with patch("urllib3.PoolManager", return_value=mock_http):
            with patch("time.sleep"):  # Speed up execution
                # Import the module
                # pylint: disable=import-outside-toplevel,import-error
                import incremental_scraper

                # Create scraper instance
                scraper = incremental_scraper.IncrementalGradCafeScraper(email="test@example.com")

                # Mock _parse_list_page to return exactly 50 results on first page
                # and empty on subsequent pages
                call_count = [0]

                def mock_parse(html):  # pylint: disable=unused-argument
                    call_count[0] += 1
                    if call_count[0] == 1:
                        # Return exactly 50 results to trigger the progress line
                        return [
                            {
                                "program": f"Program {i}",
                                "status": "Accepted",
                                "date_added": "September 20, 2025",
                                "university": f"University {i}",
                            }
                            for i in range(50)
                        ]
                    return []  # Empty for subsequent pages

                # Patch the parse method
                scraper._parse_list_page = mock_parse  # pylint: disable=protected-access

                # Capture stdout to verify the progress message
                # pylint: disable=import-outside-toplevel
                import io
                from contextlib import redirect_stdout
                # pylint: enable=import-outside-toplevel

                f = io.StringIO()
                with redirect_stdout(f):
                    # Run scrape_new_data_only
                    results = scraper.scrape_new_data_only(max_pages=5)

                output = f.getvalue()

                # Verify we got 50 results
                assert len(results) == 50

                # Verify the progress line was printed (line 163)
                assert "Progress: 50 new entries found" in output


@pytest.mark.integration
def test_scrape_with_100_results_for_multiple_progress_updates():
    """Test with 100 results to trigger progress line twice"""
    # Mock database connection
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (date(2025, 8, 1),)
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = None

    # Mock HTTP
    mock_http = MagicMock()
    mock_response = MagicMock()
    mock_response.data = b"<html><body>Test</body></html>"
    mock_response.status = 200
    mock_http.request.return_value = mock_response

    with patch("psycopg.connect", return_value=mock_conn):
        with patch("urllib3.PoolManager", return_value=mock_http):
            with patch("time.sleep"):
                # Import module
                # pylint: disable=import-outside-toplevel,import-error
                import incremental_scraper

                # Create scraper
                scraper = incremental_scraper.IncrementalGradCafeScraper(email="test@test.com")

                # Mock parse to return 50 results on first two pages
                call_count = [0]

                def mock_parse(html):  # pylint: disable=unused-argument
                    call_count[0] += 1
                    if call_count[0] <= 2:
                        # Return 50 results per page for first 2 pages
                        return [
                            {
                                "program": f"Program {i + (call_count[0]-1)*50}",
                                "status": "Accepted",
                                "date_added": "September 20, 2025",
                            }
                            for i in range(50)
                        ]
                    return []

                scraper._parse_list_page = mock_parse  # pylint: disable=protected-access

                # Capture output
                # pylint: disable=import-outside-toplevel
                import io
                from contextlib import redirect_stdout
                # pylint: enable=import-outside-toplevel

                f = io.StringIO()
                with redirect_stdout(f):
                    results = scraper.scrape_new_data_only(max_pages=5)

                output = f.getvalue()

                # Verify we got 100 results
                assert len(results) == 100

                # Verify progress lines were printed
                assert "Progress: 50 new entries found" in output
                assert "Progress: 100 new entries found" in output


@pytest.mark.integration
def test_main_with_50_results_covers_line_163():
    """Test main() function with 50 results to cover line 163"""
    # Mock database
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (date(2025, 8, 1),)
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = None

    # Mock HTTP
    mock_http = MagicMock()
    mock_response = MagicMock()
    mock_response.data = b"<html></html>"
    mock_response.status = 200
    mock_http.request.return_value = mock_response

    with patch("psycopg.connect", return_value=mock_conn):
        with patch("urllib3.PoolManager", return_value=mock_http):
            with patch("time.sleep"):
                # Clear cached import
                if "incremental_scraper" in sys.modules:
                    del sys.modules["incremental_scraper"]

                # Import module
                # pylint: disable=import-outside-toplevel,import-error
                import incremental_scraper

                # Mock parse to return exactly 50 results
                # pylint: disable=protected-access
                original_parse = incremental_scraper.IncrementalGradCafeScraper._parse_list_page
                # pylint: enable=protected-access
                call_count = [0]

                def mock_parse(self, html):  # pylint: disable=unused-argument
                    call_count[0] += 1
                    if call_count[0] == 1:
                        return [
                            {
                                "program": f"Prog{i}",
                                "status": "A",
                                "date_added": "Sep 20, 2025",
                            }
                            for i in range(50)
                        ]
                    return []

                incremental_scraper.IncrementalGradCafeScraper._parse_list_page = mock_parse  # pylint: disable=protected-access

                try:
                    # Mock file I/O
                    with patch("builtins.open", mock_open()) as m_open:
                        # Capture output
                        # pylint: disable=import-outside-toplevel
                        import io
                        from contextlib import redirect_stdout
                        # pylint: enable=import-outside-toplevel

                        f = io.StringIO()
                        with redirect_stdout(f):
                            # Run main
                            result = incremental_scraper.main()

                        output = f.getvalue()

                        # Verify result
                        assert result == 50

                        # Verify progress line was printed (line 163 covered)
                        assert "Progress: 50 new entries found" in output

                        # Verify save was called
                        m_open.assert_called_with(
                            "new_applicant_data.json", "w", encoding="utf-8"
                        )

                finally:
                    # Restore original
                    incremental_scraper.IncrementalGradCafeScraper._parse_list_page = original_parse  # pylint: disable=protected-access
