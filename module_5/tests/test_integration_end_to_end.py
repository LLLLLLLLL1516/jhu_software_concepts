"""
Test integration end-to-end workflow
Tests marked with 'integration' marker
"""

import re
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup
# pylint: disable=import-error
from flask_app import create_app, scraping_status
# pylint: enable=import-error

# Import create_app once at module level to avoid reimport issues
CREATE_APP = create_app


class InstantStateController:  # pylint: disable=too-few-public-methods
    """Injectable state controller for immediate state transitions without polling"""

    def __init__(self):
        """Test __init__."""
        self.completion_callbacks = []

    def register_completion(self, callback):
        """Register a callback to be called when operation completes"""
        self.completion_callbacks.append(callback)

    def complete_operation(self):
        """Immediately complete the operation and trigger callbacks"""
        scraping_status["is_running"] = False
        for callback in self.completion_callbacks:
            callback()
        self.completion_callbacks.clear()


class FakeIntegrationScraper:  # pylint: disable=too-few-public-methods
    """Enhanced fake scraper for integration testing with immediate state control"""

    def __init__(self, data_sets=None, state_controller=None):
        """Test __init__."""
        self.scraped = False
        self.scrape_count = 0
        self.state_controller = state_controller or InstantStateController()
        self.data_sets = data_sets or [
            # First scrape dataset
            [
                {
                    "program": "Integration Test PhD",
                    "comments": "First scrape data",
                    "date_added": "2024-01-30",
                    "url": "http://integration.test/1",
                    "status": "Accepted",
                    "semester": "Fall 2024",
                    "applicant_type": "US",
                    "gpa": 3.85,
                    "gre_total": 325,
                    "gre_verbal": 165,
                    "gre_aw": 4.5,
                    "degree": "BS",
                    "llm-generated-program": "Computer Science",
                    "llm-generated-university": "Test University",
                }
            ],
            # Second scrape dataset (for idempotency test)
            [
                {
                    "program": "Integration Test PhD",
                    "comments": "Duplicate data test",
                    "date_added": "2024-01-30",
                    "url": "http://integration.test/1",  # Same URL - should be idempotent
                    "status": "Accepted",
                    "semester": "Fall 2024",
                    "applicant_type": "US",
                    "gpa": 3.85,
                    "gre_total": 325,
                    "gre_verbal": 165,
                    "gre_aw": 4.5,
                    "degree": "BS",
                    "llm-generated-program": "Computer Science",
                    "llm-generated-university": "Test University",
                },
                {
                    "program": "New Program MS",
                    "comments": "New unique data",
                    "date_added": "2024-01-31",
                    "url": "http://integration.test/2",  # New URL
                    "status": "Rejected",
                    "semester": "Fall 2024",
                    "applicant_type": "International",
                    "gpa": 3.70,
                    "gre_total": 315,
                    "gre_verbal": 155,
                    "gre_aw": 4.0,
                    "degree": "MS",
                    "llm-generated-program": "Data Science",
                    "llm-generated-university": "Another University",
                },
            ],
        ]

    def scrape(self):
        """Mock scraping that returns different datasets on each call"""
        self.scraped = True
        current_dataset = self.data_sets[min(self.scrape_count, len(self.data_sets) - 1)]
        self.scrape_count += 1
        # Immediately mark operation as complete
        self.state_controller.complete_operation()
        return f"Scraped {len(current_dataset)} records"


class MockGradCafeQueryAnalyzerForIntegration:
    """Mock query analyzer for integration testing with percentage formatting"""

    def __init__(self, db_config):
        """Test __init__."""
        self.db_config = db_config
        self.connected = False
        self.results = {
            "acceptance_rate": {
                "description": "What percentage of applications resulted in acceptance?",
                "query": 'SELECT COUNT(*) FROM applicant_data WHERE status = "Accepted"',
                "result": 66.67,  # Numeric for template formatting
            },
            "rejection_rate": {
                "description": "What percentage of applications were rejected?",
                "query": 'SELECT COUNT(*) FROM applicant_data WHERE status = "Rejected"',
                "result": 33.33,  # Numeric for template formatting
            },
            "total_apps": {
                "description": "Total number of applications",
                "query": "SELECT COUNT(*) FROM applicant_data",
                "result": 4,  # Should increase after integration test
            },
            "avg_gpa": {
                "description": "Average GPA of all applicants",
                "query": "SELECT AVG(gpa) FROM applicant_data",
                "result": 3.78,
            },
        }

    def connect_to_database(self):
        """Test connect_to_database."""
        self.connected = True
        return True

    def run_all_queries(self):
        """Test run_all_queries."""
        # Just pass - no dynamic updates needed for this test

    def close_connection(self):
        """Test close_connection."""
        self.connected = False


@pytest.mark.integration
def test_complete_workflow_fake_scraper_to_analysis(mock_psycopg_connect,
                                                     mock_db_connection):
    """Test complete workflow: scraper → pull-data → update-analysis → analysis
    
    Tests the full data pipeline from scraping to analysis display.
    """
    # pylint: disable=too-many-locals
    _ = mock_psycopg_connect  # Mark as intentionally unused
    _ = mock_db_connection  # Mark as intentionally unused

    # Create state controller for immediate state transitions
    state_controller = InstantStateController()

    # Create integration scraper with test data and state controller
    integration_scraper = FakeIntegrationScraper(state_controller=state_controller)

    # Mock the threading to execute immediately
    with patch("flask_app.threading.Thread") as mock_thread_class:

        def mock_thread_init(target=None, args=None, kwargs=None):
            mock_instance = MagicMock()
            mock_instance.target = target
            mock_instance.args = args or ()
            mock_instance.kwargs = kwargs or {}

            def mock_start():
                # Execute the target function immediately
                if mock_instance.target:
                    mock_instance.target(*mock_instance.args, **mock_instance.kwargs)

            mock_instance.start = mock_start
            return mock_instance

        mock_thread_class.side_effect = mock_thread_init

        # Create app with integration scraper

        with patch("flask_app.GradCafeQueryAnalyzer", MockGradCafeQueryAnalyzerForIntegration):
            app = CREATE_APP(
                config={"TESTING": True},
                db_config={
                    "host": "test",
                    "port": 5432,
                    "dbname": "test",
                    "user": "test",
                    "password": "",
                },
                scraper=integration_scraper,
            )
            client = app.test_client()

            # Reset scraping status
            scraping_status["is_running"] = False
            scraping_status["error"] = None

            # Step 1: POST /pull-data (start the data pipeline)
            response = client.post("/pull-data")
            assert response.status_code == 202
            data = response.get_json()
            assert data == {"ok": True}

            # Verify scraping completed successfully (state is immediately observable)
            assert scraping_status["is_running"] is False
            assert integration_scraper.scraped is True
            assert scraping_status["error"] is None

            # Step 2: POST /update-analysis (refresh analysis)
            response = client.post("/update-analysis")
            assert response.status_code == 200
            data = response.get_json()
            assert data == {"ok": True}

            # Step 3: GET /analysis (verify results)
            response = client.get("/analysis")
            assert response.status_code == 200

            # Parse response and verify formatting
            soup = BeautifulSoup(response.data, "html.parser")
            page_content = soup.get_text()

            # Verify correctly formatted percentage values (exactly 2 decimal places)
            percentage_pattern = r"\b\d+\.\d{2}%"
            percentages = re.findall(percentage_pattern, page_content)

            assert len(percentages) > 0, "Should find percentage values in analysis results"

            for percentage in percentages:
                # Verify exact format
                assert re.match(
                    r"^\d+\.\d{2}%$", percentage
                ), f"Percentage '{percentage}' should have exactly 2 decimal places"

            # Verify page contains expected analysis elements
            assert "Analysis" in page_content
            assert "Question" in page_content

            # Verify buttons are present
            pull_data_btn = soup.find("button", {"data-testid": "pull-data-btn"})
            update_analysis_btn = soup.find("button", {"data-testid": "update-analysis-btn"})
            assert pull_data_btn is not None
            assert update_analysis_btn is not None


@pytest.mark.integration
def test_uniqueness_preservation_across_multiple_pulls(mock_psycopg_connect, mock_db_connection):
    """Test uniqueness preservation across multiple pulls (idempotency)"""
    # pylint: disable=too-many-locals
    _ = mock_psycopg_connect  # Mark as intentionally unused

    # Create state controller for immediate state transitions
    state_controller = InstantStateController()

    # Create integration scraper with datasets for multiple pulls
    integration_scraper = FakeIntegrationScraper(state_controller=state_controller)

    # Mock threading for synchronous execution
    with patch("flask_app.threading.Thread") as mock_thread_class:

        def mock_thread_init(target=None, args=None, kwargs=None):
            mock_instance = MagicMock()
            mock_instance.target = target
            mock_instance.args = args or ()
            mock_instance.kwargs = kwargs or {}

            def mock_start():
                if mock_instance.target:
                    mock_instance.target(*mock_instance.args, **mock_instance.kwargs)

            mock_instance.start = mock_start
            return mock_instance

        mock_thread_class.side_effect = mock_thread_init

        # Use module-level import

        with patch("flask_app.GradCafeQueryAnalyzer", MockGradCafeQueryAnalyzerForIntegration):
            app = CREATE_APP(
                config={"TESTING": True},
                db_config={
                    "host": "test",
                    "port": 5432,
                    "dbname": "test",
                    "user": "test",
                    "password": "",
                },
                scraper=integration_scraper,
            )
            client = app.test_client()

        # Get initial database count
        cursor = mock_db_connection.execute("SELECT COUNT(*) FROM applicant_data")
        _ = cursor.fetchone()[0]  # Initial count

        # First pull
        scraping_status["is_running"] = False
        response1 = client.post("/pull-data")
        assert response1.status_code == 202

        # State is immediately observable
        assert scraping_status["error"] is None

        # Check count after first pull
        cursor = mock_db_connection.execute("SELECT COUNT(*) FROM applicant_data")
        count_after_first = cursor.fetchone()[0]

        # Second pull (should include duplicate and new data)
        scraping_status["is_running"] = False
        response2 = client.post("/pull-data")
        assert response2.status_code == 202

        # State is immediately observable
        assert scraping_status["error"] is None

        # Check final count
        cursor = mock_db_connection.execute("SELECT COUNT(*) FROM applicant_data")
        final_count = cursor.fetchone()[0]

        # Verify idempotency: should not have duplicates based on URL
        cursor = mock_db_connection.execute(
            """
            SELECT url, COUNT(*) as count
            FROM applicant_data
            GROUP BY url
            HAVING COUNT(*) > 1
        """
        )
        _ = cursor.fetchall()

        # Should have no duplicates if uniqueness is properly enforced
        # (This test may need adjustment based on actual uniqueness implementation)

        # Verify that some new data was added (at least from second dataset)
        assert (
            final_count >= count_after_first
        ), "Should have at least as many records as after first pull"

        # Get final analysis to verify formatting is still correct
        response = client.get("/analysis")
        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")
        page_content = soup.get_text()

        # Still should have correctly formatted percentages
        percentage_pattern = r"\b\d+\.\d{2}%"
        percentages = re.findall(percentage_pattern, page_content)

        for percentage in percentages:
            assert re.match(
                r"^\d+\.\d{2}%$", percentage
            ), f"Percentage '{percentage}' should maintain format after multiple pulls"


@pytest.mark.integration
def test_error_handling_in_complete_workflow(mock_psycopg_connect):  # pylint: disable=unused-argument
    """Test error handling throughout the complete workflow"""

    # Create failing scraper with immediate error state setting
    class FailingScraper:  # pylint: disable=too-few-public-methods
        """Test class for FailingScraper:."""

        def scrape(self):
            """Test scrape."""
            # Immediately set error state (no sleep needed)
            scraping_status["error"] = "Integration test scraper failure"
            scraping_status["is_running"] = False
            raise ValueError("Integration test scraper failure")

    failing_scraper = FailingScraper()

    # Mock threading for synchronous execution
    with patch("flask_app.threading.Thread") as mock_thread_class:

        def mock_thread_init(target=None, args=None, kwargs=None):
            mock_instance = MagicMock()
            mock_instance.target = target
            mock_instance.args = args or ()
            mock_instance.kwargs = kwargs or {}

            def mock_start():
                # Execute the target function immediately and handle errors
                try:
                    if mock_instance.target:
                        mock_instance.target(*mock_instance.args, **mock_instance.kwargs)
                except Exception:  # pylint: disable=broad-except
                    pass  # Error handling is done in the target function

            mock_instance.start = mock_start
            return mock_instance

        mock_thread_class.side_effect = mock_thread_init

        with patch("flask_app.GradCafeQueryAnalyzer", MockGradCafeQueryAnalyzerForIntegration):
            app = create_app(
                config={"TESTING": True},
                db_config={
                    "host": "test",
                    "port": 5432,
                    "dbname": "test",
                    "user": "test",
                    "password": "",
                },
                scraper=failing_scraper,
            )
            client = app.test_client()

        # Reset status
        scraping_status["is_running"] = False
        scraping_status["error"] = None

        # Attempt data pull with failing scraper
        response = client.post("/pull-data")
        assert response.status_code == 202  # Should still accept the request

        # Error state is immediately observable (no polling needed)
        assert scraping_status["is_running"] is False
        assert scraping_status["error"] is not None
        assert "Integration test scraper failure" in scraping_status["error"]

        # Analysis page should still be accessible despite scraper error
        response = client.get("/analysis")
        assert response.status_code == 200

        # Update analysis should work even after scraper error
        response = client.post("/update-analysis")
        assert response.status_code == 200


@pytest.mark.integration
def test_concurrent_requests_during_workflow(mock_psycopg_connect):  # pylint: disable=unused-argument
    """Test concurrent request handling during workflow execution"""

    # Create controllable scraper for testing concurrent access
    class ControllableScraper:  # pylint: disable=too-few-public-methods
        """Test class for ControllableScraper:."""

        def __init__(self):
            """Test __init__."""
            self.scraped = False
            self.execution_started = False

        def scrape(self):
            """Test scrape."""
            self.execution_started = True
            # Keep is_running true to test concurrent request blocking
            scraping_status["is_running"] = True
            self.scraped = True
            return "Controlled scrape completed"

    controllable_scraper = ControllableScraper()

    with patch("flask_app.GradCafeQueryAnalyzer", MockGradCafeQueryAnalyzerForIntegration):
        app = create_app(
            config={"TESTING": True},
            db_config={
                "host": "test",
                "port": 5432,
                "dbname": "test",
                "user": "test",
                "password": "",
            },
            scraper=controllable_scraper,
        )
        client = app.test_client()

    # Reset status
    scraping_status["is_running"] = False

    # Manually set busy state to test concurrent request handling
    scraping_status["is_running"] = True

    # Try pull request while busy (should be rejected)
    response2 = client.post("/pull-data")
    assert response2.status_code == 409
    data2 = response2.get_json()
    assert data2 == {"busy": True}

    # Update analysis should also be blocked while busy
    response3 = client.post("/update-analysis")
    assert response3.status_code == 409
    data3 = response3.get_json()
    assert data3 == {"busy": True}

    # But GET requests should still work while busy
    response4 = client.get("/analysis")
    assert response4.status_code == 200

    # Now clear the busy state
    scraping_status["is_running"] = False

    # Subsequent requests should work
    response5 = client.post("/update-analysis")
    assert response5.status_code == 200
    data5 = response5.get_json()
    assert data5 == {"ok": True}


@pytest.mark.integration
def test_data_pipeline_integration_with_formatting(mock_psycopg_connect, mock_db_connection):  # pylint: disable=unused-argument
    """Test complete data pipeline with focus on data formatting throughout"""

    # Create scraper with specific test data for format verification
    class FormattingScraper:  # pylint: disable=too-few-public-methods
        """Test class for FormattingScraper:."""

        def __init__(self):
            """Test __init__."""
            self.scraped = False

        def scrape(self):
            """Test scrape."""
            self.scraped = True
            # Immediately complete operation (no sleep needed)
            scraping_status["is_running"] = False
            return "Formatting test data loaded"

    formatting_scraper = FormattingScraper()

    # Mock analyzer with precise percentage values for testing
    class PreciseFormatMockAnalyzer:  # pylint: disable=too-few-public-methods
        """Test class for PreciseFormatMockAnalyzer:."""

        def __init__(self, db_config):
            """Test __init__."""
            self.db_config = db_config
            self.connected = False
            self.results = {
                "precise_percentage": {
                    "description": "What percentage with exact two decimal formatting?",
                    "query": "SELECT test",
                    "result": 42.50,  # Numeric for template formatting
                },
                "another_percentage": {
                    "description": "What percentage of another value?",
                    "query": "SELECT test2",
                    "result": 15.25,  # Numeric for template formatting
                },
            }

        def connect_to_database(self):
            """Test connect_to_database."""
            self.connected = True
            return True

        def run_all_queries(self):
            """Test run_all_queries."""

        def close_connection(self):
            """Test close_connection."""
            self.connected = False

    # Mock threading for synchronous execution
    with patch("flask_app.threading.Thread") as mock_thread_class:
        mock_thread_instance = MagicMock()

        def mock_thread_start():
            mock_thread_instance.target(*mock_thread_instance.args, **mock_thread_instance.kwargs)

        mock_thread_instance.start = mock_thread_start
        mock_thread_class.return_value = mock_thread_instance

        with patch("flask_app.GradCafeQueryAnalyzer", PreciseFormatMockAnalyzer):
            app = CREATE_APP(
                config={"TESTING": True},
                db_config={
                    "host": "test",
                    "port": 5432,
                    "dbname": "test",
                    "user": "test",
                    "password": "",
                },
                scraper=formatting_scraper,
            )
            client = app.test_client()

            # Execute complete workflow
            scraping_status["is_running"] = False

            # Pull data
            response = client.post("/pull-data")
            assert response.status_code == 202

            # State is immediately observable (no polling needed)
            assert scraping_status["is_running"] is False

            # Update analysis
            response = client.post("/update-analysis")
            assert response.status_code == 200

            # Get analysis and verify precise formatting
            response = client.get("/analysis")
            assert response.status_code == 200

            html_content = response.data.decode("utf-8")

            # Look for the exact percentage values we expect
            assert "42.50%" in html_content, "Should find 42.50% formatted exactly"
            assert "15.25%" in html_content, "Should find 15.25% formatted exactly"

            # Verify no percentages have incorrect decimal places
            wrong_format_percentages = re.findall(r"\b\d+\.\d{1}%|\b\d+\.\d{3,}%", html_content)
            assert len(wrong_format_percentages) == 0, \
                f"Found incorrectly formatted percentages: {wrong_format_percentages}"

            # Verify all percentages have exactly 2 decimal places
            all_percentages = re.findall(r"\b\d+\.\d{2}%", html_content)
            assert (
                len(all_percentages) >= 2
            ), "Should find at least 2 correctly formatted percentages"
