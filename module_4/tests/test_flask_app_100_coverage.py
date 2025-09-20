"""
Comprehensive tests to achieve 100% coverage for flask_app.py
Tests all uncovered lines including error handlers, database operations, and edge cases
"""

import pytest
import os
import sys
import json
import subprocess
import threading
from unittest.mock import Mock, patch, MagicMock, mock_open, call
from datetime import datetime
import psycopg

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import after adding to path
from flask_app import create_app, scraping_status, DEFAULT_DB_CONFIG


class TestFlaskApp100Coverage:
    """Tests to achieve 100% coverage for flask_app.py"""
    
    @pytest.mark.web
    def test_create_app_with_database_url_env(self):
        """Test app creation with DATABASE_URL environment variable"""
        # Set DATABASE_URL environment variable
        test_url = "postgresql://testuser:testpass@testhost:5433/testdb"
        
        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            app = create_app()
            
            assert app.db_config['host'] == 'testhost'
            assert app.db_config['port'] == 5433
            assert app.db_config['dbname'] == 'testdb'
            assert app.db_config['user'] == 'testuser'
            assert app.db_config['password'] == 'testpass'
    
    @pytest.mark.web
    def test_create_app_with_database_url_no_password(self):
        """Test app creation with DATABASE_URL without password"""
        test_url = "postgresql://testuser@testhost:5433/testdb"
        
        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            app = create_app()
            
            assert app.db_config['host'] == 'testhost'
            assert app.db_config['port'] == 5433
            assert app.db_config['dbname'] == 'testdb'
            assert app.db_config['user'] == 'testuser'
            assert app.db_config['password'] == ''
    
    @pytest.mark.web
    def test_create_app_with_database_url_default_port(self):
        """Test app creation with DATABASE_URL using default port"""
        test_url = "postgresql://testuser:testpass@testhost/testdb"
        
        with patch.dict(os.environ, {'DATABASE_URL': test_url}):
            app = create_app()
            
            assert app.db_config['host'] == 'testhost'
            assert app.db_config['port'] == 5432  # Default port
            assert app.db_config['dbname'] == 'testdb'
    
    @pytest.mark.web
    def test_get_db_connection_failure(self):
        """Test database connection failure handling"""
        with patch('psycopg.connect', side_effect=Exception("Connection failed")):
            app = create_app(db_config={'host': 'invalid', 'port': 5432, 'dbname': 'test', 'user': 'test', 'password': ''})
            
            with app.test_client() as client:
                # Trigger a route that uses get_db_connection
                with patch('flask_app.GradCafeQueryAnalyzer') as MockAnalyzer:
                    mock_instance = MockAnalyzer.return_value
                    mock_instance.connect_to_database.return_value = False
                    
                    response = client.get('/')
                    # Should render error template
                    assert b"Failed to connect to database" in response.data
    
    @pytest.mark.web
    def test_index_route_with_exception(self):
        """Test index route exception handling"""
        app = create_app()
        
        with app.test_client() as client:
            with patch('flask_app.GradCafeQueryAnalyzer') as MockAnalyzer:
                # Make the analyzer raise an exception
                MockAnalyzer.side_effect = Exception("Test error")
                
                response = client.get('/')
                assert response.status_code == 200
                assert b"Test error" in response.data
    
    @pytest.mark.web
    def test_index_route_no_database_connection(self):
        """Test index route when database connection fails"""
        app = create_app()
        
        with app.test_client() as client:
            with patch('psycopg.connect', return_value=None):
                with patch('flask_app.GradCafeQueryAnalyzer') as MockAnalyzer:
                    mock_instance = MockAnalyzer.return_value
                    mock_instance.connect_to_database.return_value = True
                    mock_instance.run_all_queries.return_value = None
                    mock_instance.results = {}
                    
                    response = client.get('/analysis')
                    assert response.status_code == 200
                    # Should still render but with 0 records
    
    @pytest.mark.web
    def test_error_handlers(self):
        """Test 404 and 500 error handlers"""
        app = create_app()
        
        with app.test_client() as client:
            # Test 404 handler
            response = client.get('/nonexistent')
            assert response.status_code == 404
            assert b"Page not found" in response.data
            
            # Test 500 handler - trigger through a different approach
            with patch('flask_app.GradCafeQueryAnalyzer') as MockAnalyzer:
                # Force an internal server error
                mock_instance = Mock()
                mock_instance.connect_to_database.side_effect = Exception("Internal error")
                MockAnalyzer.return_value = mock_instance
                
                # The error will be caught and rendered as error template
                response = client.get('/')
                assert b"Internal error" in response.data
    
    @pytest.mark.integration
    def test_run_data_pipeline_no_new_data(self):
        """Test data pipeline when no new data is found"""
        app = create_app()
        
        with app.test_client() as client:
            # Reset status
            scraping_status['is_running'] = False
            scraping_status['error'] = None
            
            # Mock subprocess to simulate no new data
            with patch('subprocess.run') as mock_run:
                # First call returns "No new data found"
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "No new data found"
                mock_result.stderr = ""
                mock_run.return_value = mock_result
                
                with patch('threading.Thread') as MockThread:
                    # Make thread execution synchronous
                    def mock_init(target=None, **kwargs):
                        mock_thread = Mock()
                        mock_thread.target = target
                        mock_thread.daemon = True
                        
                        def mock_start():
                            target()
                        
                        mock_thread.start = mock_start
                        return mock_thread
                    
                    MockThread.side_effect = mock_init
                    
                    response = client.post('/pull-data')
                    assert response.status_code == 202
                    
                    # Check status was updated
                    assert scraping_status['progress'] == 'No new data available'
                    assert scraping_status['is_running'] == False
    
    @pytest.mark.integration
    def test_run_data_pipeline_scraping_failure(self):
        """Test data pipeline when scraping fails"""
        app = create_app()
        
        with app.test_client() as client:
            # Reset status
            scraping_status['is_running'] = False
            scraping_status['error'] = None
            
            with patch('subprocess.run') as mock_run:
                # Simulate scraping failure
                mock_result = Mock()
                mock_result.returncode = 1
                mock_result.stdout = ""
                mock_result.stderr = "Scraping error"
                mock_run.return_value = mock_result
                
                with patch('threading.Thread') as MockThread:
                    def mock_init(target=None, **kwargs):
                        mock_thread = Mock()
                        mock_thread.target = target
                        mock_thread.daemon = True
                        
                        def mock_start():
                            target()
                        
                        mock_thread.start = mock_start
                        return mock_thread
                    
                    MockThread.side_effect = mock_init
                    
                    response = client.post('/pull-data')
                    assert response.status_code == 202
                    
                    # Check error was captured
                    assert scraping_status['error'] is not None
                    assert 'Scraping failed' in scraping_status['error']
    
    @pytest.mark.integration
    def test_run_data_pipeline_cleaning_failure(self):
        """Test data pipeline when cleaning fails"""
        app = create_app()
        
        with app.test_client() as client:
            scraping_status['is_running'] = False
            scraping_status['error'] = None
            
            with patch('subprocess.run') as mock_run:
                def side_effect(*args, **kwargs):
                    # First call (scraping) succeeds
                    if 'incremental_scraper.py' in args[0]:
                        result = Mock()
                        result.returncode = 0
                        result.stdout = "Found new data"
                        result.stderr = ""
                        return result
                    # Second call (cleaning) fails
                    elif 'clean.py' in args[0]:
                        result = Mock()
                        result.returncode = 1
                        result.stdout = ""
                        result.stderr = "Cleaning error"
                        return result
                    return Mock(returncode=0, stdout="", stderr="")
                
                mock_run.side_effect = side_effect
                
                with patch('threading.Thread') as MockThread:
                    def mock_init(target=None, **kwargs):
                        mock_thread = Mock()
                        mock_thread.target = target
                        mock_thread.daemon = True
                        
                        def mock_start():
                            target()
                        
                        mock_thread.start = mock_start
                        return mock_thread
                    
                    MockThread.side_effect = mock_init
                    
                    response = client.post('/pull-data')
                    assert response.status_code == 202
                    
                    assert scraping_status['error'] is not None
                    assert 'Cleaning failed' in scraping_status['error']
    
    @pytest.mark.integration
    def test_run_data_pipeline_llm_failure(self):
        """Test data pipeline when LLM processing fails"""
        app = create_app()
        
        with app.test_client() as client:
            scraping_status['is_running'] = False
            scraping_status['error'] = None
            
            with patch('subprocess.run') as mock_run:
                def side_effect(*args, **kwargs):
                    # Scraping succeeds
                    if 'incremental_scraper.py' in args[0]:
                        return Mock(returncode=0, stdout="Found new data", stderr="")
                    # Cleaning succeeds
                    elif 'clean.py' in args[0]:
                        return Mock(returncode=0, stdout="Cleaned", stderr="")
                    # LLM fails
                    elif 'app.py' in args[0]:
                        return Mock(returncode=1, stdout="", stderr="LLM error")
                    return Mock(returncode=0, stdout="", stderr="")
                
                mock_run.side_effect = side_effect
                
                with patch('threading.Thread') as MockThread:
                    def mock_init(target=None, **kwargs):
                        mock_thread = Mock()
                        mock_thread.target = target
                        mock_thread.daemon = True
                        
                        def mock_start():
                            target()
                        
                        mock_thread.start = mock_start
                        return mock_thread
                    
                    MockThread.side_effect = mock_init
                    
                    response = client.post('/pull-data')
                    assert response.status_code == 202
                    
                    assert scraping_status['error'] is not None
                    assert 'LLM processing failed' in scraping_status['error']
    
    @pytest.mark.integration
    def test_run_data_pipeline_complete_success(self):
        """Test complete data pipeline success with database loading"""
        app = create_app()
        
        with app.test_client() as client:
            scraping_status['is_running'] = False
            scraping_status['error'] = None
            
            with patch('subprocess.run') as mock_run:
                # All subprocess calls succeed
                mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")
                
                # Mock file operations
                with patch('builtins.open', mock_open()):
                    # Mock database operations - patch at import location
                    with patch('load_data.GradCafeDataLoader') as MockLoader:
                        mock_loader = MockLoader.return_value
                        mock_loader.connect_to_database.return_value = True
                        mock_loader.load_data_from_jsonl.return_value = True
                        mock_loader.close_connection.return_value = None
                        
                        # Mock psycopg connection for counting
                        with patch('psycopg.connect') as mock_connect:
                            mock_conn = Mock()
                            mock_cursor = Mock()
                            mock_cursor.fetchone.side_effect = [(100,), (110,)]  # Initial and final counts
                            mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
                            mock_conn.cursor.return_value.__exit__ = Mock(return_value=None)
                            mock_conn.close = Mock()
                            mock_connect.return_value = mock_conn
                            
                            with patch('threading.Thread') as MockThread:
                                def mock_init(target=None, **kwargs):
                                    mock_thread = Mock()
                                    mock_thread.target = target
                                    mock_thread.daemon = True
                                    
                                    def mock_start():
                                        target()
                                    
                                    mock_thread.start = mock_start
                                    return mock_thread
                                
                                MockThread.side_effect = mock_init
                                
                                response = client.post('/pull-data')
                                assert response.status_code == 202
                                
                                # Check success status
                                assert scraping_status['error'] is None
                                assert 'Complete! Added 10 new records' in scraping_status['progress']
    
    @pytest.mark.integration
    def test_load_new_data_database_connection_failure(self):
        """Test load_new_data_to_database when connection fails"""
        app = create_app()
        
        with app.test_client() as client:
            scraping_status['is_running'] = False
            
            with patch('subprocess.run') as mock_run:
                # All subprocess calls succeed
                mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")
                
                with patch('builtins.open', mock_open()):
                    with patch('load_data.GradCafeDataLoader') as MockLoader:
                        mock_loader = MockLoader.return_value
                        mock_loader.connect_to_database.return_value = False  # Connection fails
                        
                        with patch('threading.Thread') as MockThread:
                            def mock_init(target=None, **kwargs):
                                mock_thread = Mock()
                                mock_thread.target = target
                                mock_thread.daemon = True
                                
                                def mock_start():
                                    target()
                                
                                mock_thread.start = mock_start
                                return mock_thread
                            
                            MockThread.side_effect = mock_init
                            
                            response = client.post('/pull-data')
                            assert response.status_code == 202
                            
                            assert scraping_status['error'] is not None
                            assert 'Failed to connect to database' in scraping_status['error']
    
    @pytest.mark.integration
    def test_load_new_data_loading_failure(self):
        """Test load_new_data_to_database when data loading fails"""
        app = create_app()
        
        with app.test_client() as client:
            scraping_status['is_running'] = False
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")
                
                with patch('builtins.open', mock_open()):
                    with patch('load_data.GradCafeDataLoader') as MockLoader:
                        mock_loader = MockLoader.return_value
                        mock_loader.connect_to_database.return_value = True
                        mock_loader.load_data_from_jsonl.return_value = False  # Loading fails
                        
                        with patch('threading.Thread') as MockThread:
                            def mock_init(target=None, **kwargs):
                                mock_thread = Mock()
                                mock_thread.target = target
                                mock_thread.daemon = True
                                
                                def mock_start():
                                    target()
                                
                                mock_thread.start = mock_start
                                return mock_thread
                            
                            MockThread.side_effect = mock_init
                            
                            response = client.post('/pull-data')
                            assert response.status_code == 202
                            
                            assert scraping_status['error'] is not None
                            assert 'Database loading error' in scraping_status['error']
    
    @pytest.mark.web
    def test_main_execution(self):
        """Test main execution block"""
        # Test the if __name__ == '__main__' block
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'flask_app.py')
        
        with patch('flask.Flask.run') as mock_run:
            # Read the file
            with open(src_path, 'r') as f:
                code = f.read()
            
            # Create a namespace for execution
            namespace = {'__name__': '__main__', '__file__': src_path}
            
            # Execute the code
            exec(compile(code, src_path, 'exec'), namespace)
            
            # Verify app.run was called with correct parameters
            mock_run.assert_called_with(host='0.0.0.0', port=8080, debug=True)
    
    @pytest.mark.web
    def test_500_error_handler(self):
        """Test 500 error handler directly"""
        app = create_app()
        
        # Get the 500 error handler
        with app.test_request_context():
            # Manually trigger the 500 handler
            from werkzeug.exceptions import InternalServerError
            
            # Call the error handler directly
            handlers = app.error_handler_spec[None][500]
            if handlers:
                handler = handlers[InternalServerError]
                response = handler(InternalServerError())
                # Response is a tuple (html, status_code)
                assert response[1] == 500
                assert "Internal server error" in response[0]
    
    @pytest.mark.integration
    def test_load_new_data_exception_handling(self):
        """Test exception handling in load_new_data_to_database"""
        app = create_app()
        
        with app.test_client() as client:
            scraping_status['is_running'] = False
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")
                
                with patch('builtins.open', mock_open()):
                    # Make GradCafeDataLoader raise an exception
                    with patch('load_data.GradCafeDataLoader', side_effect=Exception("Import error")):
                        with patch('threading.Thread') as MockThread:
                            def mock_init(target=None, **kwargs):
                                mock_thread = Mock()
                                mock_thread.target = target
                                mock_thread.daemon = True
                                
                                def mock_start():
                                    target()
                                
                                mock_thread.start = mock_start
                                return mock_thread
                            
                            MockThread.side_effect = mock_init
                            
                            response = client.post('/pull-data')
                            assert response.status_code == 202
                            
                            assert scraping_status['error'] is not None
                            assert 'Database loading error' in scraping_status['error']
    
    @pytest.mark.web
    def test_get_db_connection_success(self):
        """Test successful database connection - covers lines 67-69"""
        # We need to patch psycopg at the module level where it's imported
        with patch('flask_app.psycopg') as mock_psycopg:
            # Create a mock connection object
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchone.side_effect = [(100,), (datetime.now(),)]
            mock_cursor.execute = Mock()
            mock_conn.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = Mock(return_value=None)
            mock_conn.close = Mock()
            
            # Make psycopg.connect return our mock connection
            mock_psycopg.connect.return_value = mock_conn
            
            # Create app after patching
            app = create_app()
            
            with app.test_client() as client:
                with patch('flask_app.GradCafeQueryAnalyzer') as MockAnalyzer:
                    mock_instance = MockAnalyzer.return_value
                    mock_instance.connect_to_database.return_value = True
                    mock_instance.run_all_queries.return_value = None
                    mock_instance.results = {}
                    mock_instance.close_connection.return_value = None
                    
                    # Make the request which should trigger get_db_connection()
                    response = client.get('/')
                    assert response.status_code == 200
                    
                    # Verify psycopg.connect was called (lines 67-69 executed)
                    mock_psycopg.connect.assert_called()
                    # The connection should have been returned successfully
                    assert mock_conn.cursor.called
                    assert mock_conn.close.called
    
    @pytest.mark.db
    def test_index_route_with_successful_db_connection(self):
        """Test index route with successful database connection to ensure lines 67-69 are covered"""
        # Patch at the module level
        with patch('flask_app.psycopg') as mock_psycopg:
            # Create successful connection mock
            mock_conn = Mock()
            mock_cursor = Mock()
            # Set up cursor to return data
            mock_cursor.fetchone.side_effect = [(150,), (datetime(2024, 1, 1),)]
            mock_cursor.execute = Mock()
            mock_cursor.__enter__ = Mock(return_value=mock_cursor)
            mock_cursor.__exit__ = Mock(return_value=None)
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.close = Mock()
            
            # Configure psycopg.connect to return our mock
            mock_psycopg.connect.return_value = mock_conn
            
            # Create app with custom db config
            test_db_config = {
                'host': 'testhost',
                'port': 5432,
                'dbname': 'testdb',
                'user': 'testuser',
                'password': 'testpass'
            }
            app = create_app(db_config=test_db_config)
            
            with app.test_client() as client:
                with patch('flask_app.GradCafeQueryAnalyzer') as MockAnalyzer:
                    mock_analyzer = MockAnalyzer.return_value
                    mock_analyzer.connect_to_database.return_value = True
                    mock_analyzer.run_all_queries.return_value = None
                    mock_analyzer.results = {'test': 'data'}
                    mock_analyzer.close_connection.return_value = None
                    
                    # Make request
                    response = client.get('/analysis')
                    
                    # Should be successful
                    assert response.status_code == 200
                    
                    # Verify database was connected to successfully
                    mock_psycopg.connect.assert_called_with(**test_db_config)
                    assert mock_conn.cursor.called
                    assert mock_cursor.execute.call_count == 2  # Two queries in index route
                    assert mock_conn.close.called
