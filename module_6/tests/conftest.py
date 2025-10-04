"""
Test configuration and fixtures for Module 4 Flask app tests
"""

import os
import sqlite3
import sys
from unittest.mock import patch

import pytest

# Add src directory to path for importing application modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# pylint: disable=import-error,wrong-import-position
from flask_app import create_app, scraping_status
# pylint: enable=import-error
# pylint: disable=redefined-outer-name,too-few-public-methods


class FakeScraper:
    """Fake scraper for dependency injection in tests"""

    def __init__(self, should_fail=False, data_count=10):
        """Test __init__."""
        self.should_fail = should_fail
        self.data_count = data_count
        self.scraped = False

    def scrape(self):
        """Mock scraping operation"""
        if self.should_fail:
            raise ValueError("Test scraping failure")
        self.scraped = True
        # Simulate data loading
        return f"Scraped {self.data_count} records"


class MockGradCafeQueryAnalyzer:
    """Mock query analyzer for testing"""

    def __init__(self, db_config):
        """Test __init__."""
        self.db_config = db_config
        self.connected = False
        self.results = {
            "query1": {
                "description": "What percentage of applications resulted in acceptance?",
                "query": 'SELECT COUNT(*) FROM applicant_data WHERE status = "Accepted"',
                "result": "15.25",
            },
            "query2": {
                "description": "Average GPA of accepted applicants",
                "query": 'SELECT AVG(gpa) FROM applicant_data WHERE status = "Accepted"',
                "result": "3.75",
            },
            "query3": {
                "description": "Total number of applications in database",
                "query": "SELECT COUNT(*) FROM applicant_data",
                "result": 1500,
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


@pytest.fixture
def mock_db_config():
    """Provide a mock database configuration"""
    return {
        "host": "test_host",
        "port": 5432,
        "dbname": "test_db",
        "user": "test_user",
        "password": "test_pass",
    }


@pytest.fixture
def fake_scraper():
    """Provide a fake scraper instance"""
    return FakeScraper()


@pytest.fixture
def fake_failing_scraper():
    """Provide a fake scraper that fails"""
    return FakeScraper(should_fail=True)


@pytest.fixture
def mock_query_analyzer():
    """Provide a mock query analyzer"""
    return MockGradCafeQueryAnalyzer


@pytest.fixture
def app_config():
    """Provide test configuration for Flask app"""
    return {"TESTING": True, "WTF_CSRF_ENABLED": False}


@pytest.fixture
def app(mock_db_config, fake_scraper, mock_query_analyzer, app_config):
    """Create Flask app instance for testing"""

    # Reset scraping status for each test
    scraping_status["is_running"] = False
    scraping_status["progress"] = ""
    scraping_status["last_update"] = None
    scraping_status["error"] = None

    # Patch the query analyzer
    with patch("flask_app.GradCafeQueryAnalyzer", mock_query_analyzer):
        app = create_app(config=app_config, db_config=mock_db_config, scraper=fake_scraper)
        yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_db_connection():
    """Mock database connection with in-memory SQLite"""
    # Create in-memory SQLite database for testing
    conn = sqlite3.connect(":memory:")

    # Create test table matching PostgreSQL schema
    conn.execute(
        """
        CREATE TABLE applicant_data (
            p_id INTEGER PRIMARY KEY,
            program TEXT,
            comments TEXT,
            date_added DATE,
            url TEXT,
            status TEXT,
            term TEXT,
            us_or_international TEXT,
            gpa REAL,
            gre REAL,
            gre_v REAL,
            gre_aw REAL,
            degree TEXT,
            llm_generated_program TEXT,
            llm_generated_university TEXT
        )
    """
    )

    # Insert sample test data
    test_data = [
        (
            "Computer Science PhD",
            "Great program!",
            "2024-01-15",
            "http://test.com/1",
            "Accepted",
            "Fall 2024",
            "US",
            3.85,
            325.0,
            165.0,
            4.5,
            "BS",
            "Computer Science",
            "Stanford University",
        ),
        (
            "Data Science MS",
            "Good fit",
            "2024-01-16",
            "http://test.com/2",
            "Rejected",
            "Fall 2024",
            "International",
            3.65,
            315.0,
            155.0,
            4.0,
            "BS",
            "Data Science",
            "MIT",
        ),
        (
            "AI PhD",
            "Dream school",
            "2024-01-17",
            "http://test.com/3",
            "Accepted",
            "Fall 2024",
            "US",
            3.92,
            335.0,
            170.0,
            5.0,
            "MS",
            "Artificial Intelligence",
            "Carnegie Mellon",
        ),
    ]

    conn.executemany(
        """
        INSERT INTO applicant_data (
            program, comments, date_added, url, status, term, us_or_international,
            gpa, gre, gre_v, gre_aw, degree, llm_generated_program, llm_generated_university
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        test_data,
    )

    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def mock_psycopg_connect(mock_db_connection):
    """Mock psycopg.connect to return SQLite connection"""

    class MockCursor:
        """Mock cursor for SQLite connection."""

        def __init__(self, connection):
            """Initialize mock cursor."""
            self.connection = connection
            self.last_cursor = None

        def execute(self, query, params=None):
            """Execute a query."""
            # Simple query translation for basic operations
            if params:
                self.last_cursor = self.connection.execute(query, params)
            else:
                self.last_cursor = self.connection.execute(query)
            return self.last_cursor

        def executemany(self, query, params):
            """Execute many queries."""
            self.last_cursor = self.connection.executemany(query, params)
            return self.last_cursor

        def fetchone(self):
            """Fetch one result."""
            if self.last_cursor:
                return self.last_cursor.fetchone()
            return None

        def fetchall(self):
            """Fetch all results."""
            if self.last_cursor:
                return self.last_cursor.fetchall()
            return []

        def __enter__(self):
            """Enter context manager."""
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Exit context manager."""

    class MockConnection:
        """Mock database connection."""

        def __init__(self, sqlite_conn):
            """Initialize mock connection."""
            self.sqlite_conn = sqlite_conn

        def cursor(self):
            """Get cursor."""
            return MockCursor(self.sqlite_conn)

        def commit(self):
            """Commit transaction."""
            self.sqlite_conn.commit()

        def rollback(self):
            """Rollback transaction."""
            self.sqlite_conn.rollback()

        def close(self):
            """Close connection."""
            # Don't close the test connection

        def __enter__(self):
            """Enter context manager."""
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Exit context manager."""

    def mock_connect(**_):  # pylint: disable=unused-argument
        return MockConnection(mock_db_connection)

    with patch("psycopg.connect", mock_connect):
        yield mock_connect


@pytest.fixture(autouse=True)
def reset_scraping_status():
    """Reset scraping status before each test"""
    scraping_status["is_running"] = False
    scraping_status["progress"] = ""
    scraping_status["last_update"] = None
    scraping_status["error"] = None
    yield
    # Reset after test as well
    scraping_status["is_running"] = False
    scraping_status["progress"] = ""
    scraping_status["last_update"] = None
    scraping_status["error"] = None
