"""
Targeted test to cover the exception handling in get_db_connection()
Lines 67-69 in flask_app.py
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from io import StringIO

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask_app import create_app


class TestFlaskAppExceptionCoverage:
    """Test to cover exception handling in get_db_connection (lines 67-69)"""
    
    @pytest.mark.db
    def test_get_db_connection_exception(self):
        """Test database connection failure - covers lines 67-69"""
        # Patch psycopg to raise an exception when connect is called
        with patch('flask_app.psycopg') as mock_psycopg:
            # Make psycopg.connect raise an exception
            mock_psycopg.connect.side_effect = Exception("Database connection failed")
            
            # Create app after patching
            app = create_app()
            
            with app.test_client() as client:
                # Patch print to capture the error message
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    # Mock GradCafeQueryAnalyzer to avoid other errors
                    with patch('flask_app.GradCafeQueryAnalyzer') as MockAnalyzer:
                        mock_analyzer = MagicMock()
                        mock_analyzer.connect_to_database.return_value = True
                        mock_analyzer.run_all_queries = MagicMock()
                        mock_analyzer.results = {}
                        mock_analyzer.close_connection = MagicMock()
                        MockAnalyzer.return_value = mock_analyzer
                        
                        # Make request to trigger get_db_connection()
                        response = client.get('/')
                        
                        # Should still return 200 (handled gracefully)
                        assert response.status_code == 200
                        
                        # Verify the exception was caught and printed
                        output = mock_stdout.getvalue()
                        assert "Database connection error: Database connection failed" in output
                        
                        # Verify psycopg.connect was called and raised exception
                        mock_psycopg.connect.assert_called()
    
    @pytest.mark.db
    def test_index_route_with_db_connection_failure(self):
        """Test index route when get_db_connection fails - ensures lines 67-69 are covered"""
        with patch('flask_app.psycopg') as mock_psycopg:
            # Make connect raise an exception
            mock_psycopg.connect.side_effect = Exception("Connection refused")
            
            app = create_app()
            
            with app.test_client() as client:
                with patch('flask_app.GradCafeQueryAnalyzer') as MockAnalyzer:
                    mock_analyzer = MagicMock()
                    mock_analyzer.connect_to_database.return_value = True
                    mock_analyzer.run_all_queries = MagicMock()
                    mock_analyzer.results = {'test': 'data'}
                    mock_analyzer.close_connection = MagicMock()
                    MockAnalyzer.return_value = mock_analyzer
                    
                    # Capture print output
                    with patch('builtins.print') as mock_print:
                        response = client.get('/analysis')
                        
                        # Should handle gracefully
                        assert response.status_code == 200
                        
                        # Verify error was printed
                        mock_print.assert_any_call("Database connection error: Connection refused")
                        
                        # The template should render with 0 records since conn is None
                        assert b"0" in response.data or b"None" in response.data
    
    @pytest.mark.integration
    def test_load_new_data_with_db_connection_failure(self):
        """Test load_new_data_to_database when get_db_connection fails"""
        with patch('flask_app.psycopg') as mock_psycopg:
            # First call succeeds for GradCafeDataLoader, subsequent calls fail
            call_count = [0]
            
            def connect_side_effect(**kwargs):
                call_count[0] += 1
                if call_count[0] <= 1:
                    # First call for GradCafeDataLoader succeeds
                    mock_conn = MagicMock()
                    return mock_conn
                else:
                    # Subsequent calls for get_db_connection fail
                    raise Exception("Database unavailable")
            
            mock_psycopg.connect.side_effect = connect_side_effect
            
            app = create_app()
            
            with app.test_client() as client:
                from flask_app import scraping_status
                scraping_status['is_running'] = False
                
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")
                    
                    with patch('builtins.open', create=True) as mock_open:
                        mock_file = MagicMock()
                        mock_file.write = MagicMock()
                        mock_file.__enter__ = MagicMock(return_value=mock_file)
                        mock_file.__exit__ = MagicMock(return_value=None)
                        mock_open.return_value = mock_file
                        
                        with patch('load_data.GradCafeDataLoader') as MockLoader:
                            mock_loader = MagicMock()
                            mock_loader.connect_to_database.return_value = True
                            mock_loader.load_data_from_jsonl.return_value = True
                            mock_loader.close_connection = MagicMock()
                            MockLoader.return_value = mock_loader
                            
                            with patch('threading.Thread') as MockThread:
                                def run_sync(target=None, **kwargs):
                                    thread = MagicMock()
                                    thread.daemon = True
                                    thread.start = lambda: target()
                                    return thread
                                
                                MockThread.side_effect = run_sync
                                
                                with patch('builtins.print') as mock_print:
                                    # Trigger the pipeline
                                    response = client.post('/pull-data')
                                    assert response.status_code == 202
                                    
                                    # Verify database connection error was printed
                                    # This confirms lines 67-69 were executed
                                    error_prints = [call for call in mock_print.call_args_list 
                                                  if "Database connection error" in str(call)]
                                    assert len(error_prints) > 0
                                    
                                    # The pipeline should have failed due to DB connection issues
                                    assert scraping_status['error'] is not None
