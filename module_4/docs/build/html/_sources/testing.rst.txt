Testing Guide
=============

This guide explains how to run tests for the GradCafe Data Analysis system, including marked tests, expected selectors, and test doubles/fixtures.

Test Organization
-----------------

Tests are organized by functionality and marked with specific categories:

* ``@pytest.mark.web`` - Page load and HTML structure tests
* ``@pytest.mark.buttons`` - Button endpoints and busy-state behavior tests
* ``@pytest.mark.analysis`` - Labels and percentage formatting tests
* ``@pytest.mark.db`` - Database schema/inserts/selects tests
* ``@pytest.mark.integration`` - End-to-end flow tests

Running Tests
-------------

Basic Test Execution
~~~~~~~~~~~~~~~~~~~~

Run all tests:

.. code-block:: bash

   pytest tests/ -v

Run tests with coverage:

.. code-block:: bash

   pytest tests/ --cov=src --cov-report=html

Running Marked Tests
~~~~~~~~~~~~~~~~~~~~

Run specific categories of tests using marks:

.. code-block:: bash

   # Run only web tests
   pytest tests/ -m web -v
   
   # Run only database tests
   pytest tests/ -m db -v
   
   # Run only button tests
   pytest tests/ -m buttons -v
   
   # Run only analysis tests
   pytest tests/ -m analysis -v
   
   # Run only integration tests
   pytest tests/ -m integration -v

Combine multiple marks:

.. code-block:: bash

   # Run web and buttons tests
   pytest tests/ -m "web or buttons" -v
   
   # Run all except integration tests
   pytest tests/ -m "not integration" -v

Test Configuration
------------------

pytest.ini Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

The ``pytest.ini`` file configures test behavior:

.. code-block:: ini

   [pytest]
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   markers =
       web: marks tests for web page functionality
       buttons: marks tests for button endpoints
       analysis: marks tests for analysis formatting
       db: marks tests for database operations
       integration: marks tests for end-to-end flows
   addopts = -v --tb=short

Coverage Configuration
~~~~~~~~~~~~~~~~~~~~~~

The ``.coveragerc`` file configures coverage reporting:

.. code-block:: ini

   [run]
   source = src
   omit = 
       */tests/*
       */test_*.py
       */__pycache__/*
       */venv/*
   
   [report]
   exclude_lines =
       pragma: no cover
       def __repr__
       raise AssertionError
       raise NotImplementedError
       if __name__ == .__main__.:

Test Doubles and Fixtures
--------------------------

The test suite uses dependency injection and fixtures to avoid external dependencies.

Common Fixtures
~~~~~~~~~~~~~~~

Located in ``tests/conftest.py``:

.. code-block:: python

   @pytest.fixture
   def mock_scraper():
       """Mock scraper that returns test data."""
       scraper = Mock(spec=GradCafeListScraper)
       scraper.scrape_all_pages.return_value = [
           {"university": "Test U", "program": "CS", "decision": "Accepted"}
       ]
       return scraper
   
   @pytest.fixture
   def test_db_config():
       """Test database configuration."""
       return {
           'host': 'localhost',
           'port': 5432,
           'dbname': 'test_gradcafe',
           'user': 'test_user',
           'password': 'test_pass'
       }
   
   @pytest.fixture
   def app(mock_scraper, test_db_config):
       """Create test Flask application."""
       from flask_app import create_app
       app = create_app(scraper=mock_scraper, db_config=test_db_config)
       app.config['TESTING'] = True
       return app
   
   @pytest.fixture
   def client(app):
       """Create test client."""
       return app.test_client()

Mock Objects
~~~~~~~~~~~~

Tests use mock objects to simulate external dependencies:

.. code-block:: python

   # Mock database connection
   @patch('psycopg2.connect')
   def test_database_operation(mock_connect):
       mock_conn = Mock()
       mock_cursor = Mock()
       mock_connect.return_value = mock_conn
       mock_conn.cursor.return_value = mock_cursor
       
       # Test database operation
       loader = GradCafeDataLoader(db_config)
       loader.connect_to_database()
       
       assert mock_connect.called
   
   # Mock file operations
   @patch('builtins.open', new_callable=mock_open)
   def test_file_operation(mock_file):
       cleaner = GradCafeDataCleaner("test.json")
       cleaner.save_cleaned_data("output.json")
       
       mock_file.assert_called_with("output.json", 'w')

Expected Selectors
------------------

HTML Element Selectors
~~~~~~~~~~~~~~~~~~~~~~

Tests verify specific HTML elements using BeautifulSoup:

.. code-block:: python

   def test_page_structure(client):
       """Test HTML structure contains expected elements."""
       response = client.get('/')
       soup = BeautifulSoup(response.data, 'html.parser')
       
       # Check for required elements
       assert soup.find('button', id='pull-data-btn')
       assert soup.find('button', id='update-analysis-btn')
       assert soup.find('div', id='status-message')
       assert soup.find('div', id='analysis-results')

CSS Selectors
~~~~~~~~~~~~~

.. code-block:: python

   # Expected CSS classes
   EXPECTED_CLASSES = {
       'btn-primary': 'Primary action buttons',
       'btn-disabled': 'Disabled state for buttons',
       'status-running': 'Running operation indicator',
       'status-error': 'Error state indicator',
       'analysis-table': 'Results table styling'
   }

Data Attributes
~~~~~~~~~~~~~~~

.. code-block:: python

   # Expected data attributes
   EXPECTED_ATTRIBUTES = {
       'data-action': 'Action identifier for buttons',
       'data-status': 'Current operation status',
       'data-timestamp': 'Last update timestamp'
   }

Test Patterns
-------------

Testing Busy State
~~~~~~~~~~~~~~~~~~

Tests verify busy-state behavior without using sleep():

.. code-block:: python

   def test_busy_state_injection(client):
       """Test busy state through dependency injection."""
       # Inject busy state
       with client.application.app_context():
           client.application.config['IS_RUNNING'] = True
       
       # Verify busy response
       response = client.post('/pull-data')
       data = json.loads(response.data)
       
       assert response.status_code == 409
       assert data['busy'] is True

Testing Percentage Formatting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use regex to verify two-decimal percentage format:

.. code-block:: python

   import re
   
   def test_percentage_format(client):
       """Test percentage formatting in analysis."""
       response = client.get('/')
       html = response.data.decode('utf-8')
       
       # Regex for XX.XX% format
       percentage_pattern = r'\d{1,2}\.\d{2}%'
       matches = re.findall(percentage_pattern, html)
       
       assert len(matches) > 0
       for match in matches:
           # Verify format
           assert re.match(r'^\d{1,2}\.\d{2}%$', match)

Database Testing
~~~~~~~~~~~~~~~~

Tests use transaction rollback for isolation:

.. code-block:: python

   @pytest.fixture
   def db_session():
       """Create isolated database session."""
       connection = create_connection(test_db_config)
       transaction = connection.begin()
       
       yield connection
       
       # Rollback after test
       transaction.rollback()
       connection.close()
   
   def test_database_insert(db_session):
       """Test database insertion with rollback."""
       cursor = db_session.cursor()
       cursor.execute("INSERT INTO admission_results ...")
       
       # Verify insertion
       cursor.execute("SELECT COUNT(*) FROM admission_results")
       count = cursor.fetchone()[0]
       assert count == 1
       # Changes will be rolled back after test

Integration Testing
~~~~~~~~~~~~~~~~~~~

End-to-end tests verify complete workflows:

.. code-block:: python

   @pytest.mark.integration
   def test_full_data_pipeline():
       """Test complete ETL pipeline."""
       # 1. Scrape data
       scraper = MockScraper()
       data = scraper.scrape_all_pages()
       
       # 2. Clean data
       cleaner = DataCleaner(data)
       cleaned = cleaner.clean_all_data()
       
       # 3. Load to database
       loader = DataLoader(test_db_config)
       loader.insert_data(cleaned)
       
       # 4. Query analysis
       analyzer = QueryAnalyzer(test_db_config)
       results = analyzer.run_all_queries()
       
       # 5. Verify results
       assert len(results) > 0
       assert 'acceptance_rate' in results

Best Practices
--------------

1. **Test Isolation**: Each test should be independent
2. **No External Dependencies**: Use mocks for external services
3. **Fast Execution**: Avoid sleep() and long-running operations
4. **Clear Assertions**: Use descriptive assertion messages
5. **Proper Cleanup**: Use fixtures for setup/teardown
6. **Comprehensive Coverage**: Aim for 100% code coverage

Common Testing Commands
-----------------------

.. code-block:: bash

   # Run all tests with verbose output
   pytest tests/ -v
   
   # Run with coverage report
   pytest tests/ --cov=src --cov-report=term-missing
   
   # Generate HTML coverage report
   pytest tests/ --cov=src --cov-report=html
   
   # Run specific test file
   pytest tests/test_flask_app.py -v
   
   # Run tests matching pattern
   pytest tests/ -k "test_button" -v
   
   # Run with specific mark
   pytest tests/ -m web -v
   
   # Show test durations
   pytest tests/ --durations=10
   
   # Run in parallel (requires pytest-xdist)
   pytest tests/ -n auto

Troubleshooting Tests
---------------------

Common Issues
~~~~~~~~~~~~~

**Import Errors**
   Ensure PYTHONPATH includes the src directory:
   
   .. code-block:: bash
   
      export PYTHONPATH=$PYTHONPATH:./src

**Database Connection Errors**
   Tests should use mock database connections:
   
   .. code-block:: python
   
      @patch('psycopg2.connect')
      def test_db_operation(mock_connect):
          # Test without real database

**Flaky Tests**
   Avoid time-dependent or order-dependent tests:
   
   .. code-block:: python
   
      # Bad: Depends on current time
      assert datetime.now().hour == 10
      
      # Good: Mock time
      with freeze_time("2025-01-01 10:00:00"):
          assert datetime.now().hour == 10

**Coverage Gaps**
   Check coverage report for untested code:
   
   .. code-block:: bash
   
      pytest --cov=src --cov-report=term-missing

Continuous Integration
----------------------

Example GitHub Actions workflow:

.. code-block:: yaml

   name: Tests
   
   on: [push, pull_request]
   
   jobs:
     test:
       runs-on: ubuntu-latest
       
       steps:
       - uses: actions/checkout@v2
       
       - name: Set up Python
         uses: actions/setup-python@v2
         with:
           python-version: '3.8'
       
       - name: Install dependencies
         run: |
           pip install -r requirements.txt
           pip install pytest pytest-cov
       
       - name: Run tests
         run: |
           pytest tests/ --cov=src --cov-report=xml
       
       - name: Upload coverage
         uses: codecov/codecov-action@v2
