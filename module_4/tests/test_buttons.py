"""
Test button functionality and API endpoints
Tests marked with 'buttons' marker
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask_app import scraping_status


@pytest.mark.buttons
def test_pull_data_endpoint_success_when_not_busy(client, fake_scraper, mock_psycopg_connect):
    """Test POST /pull-data returns 202 with {'ok': True} when not busy"""
    # Ensure not busy
    scraping_status['is_running'] = False
    
    response = client.post('/pull-data', json={})
    
    assert response.status_code == 202
    assert response.is_json
    
    data = response.get_json()
    assert data == {'ok': True}


@pytest.mark.buttons
def test_pull_data_endpoint_busy_response(client, fake_scraper, mock_psycopg_connect):
    """Test POST /pull-data returns 409 with {'busy': True} when pull is in progress"""
    # Set as busy
    scraping_status['is_running'] = True
    
    response = client.post('/pull-data', json={})
    
    assert response.status_code == 409
    assert response.is_json
    
    data = response.get_json()
    assert data == {'busy': True}


@pytest.mark.buttons
def test_update_analysis_endpoint_success_when_not_busy(client, fake_scraper, mock_psycopg_connect):
    """Test POST /update-analysis returns 200 with {'ok': True} when not busy"""
    # Ensure not busy
    scraping_status['is_running'] = False
    
    response = client.post('/update-analysis', json={})
    
    assert response.status_code == 200
    assert response.is_json
    
    data = response.get_json()
    assert data == {'ok': True}


@pytest.mark.buttons
def test_update_analysis_endpoint_busy_response(client, fake_scraper, mock_psycopg_connect):
    """Test POST /update-analysis returns 409 with {'busy': True} when pull is in progress"""
    # Set as busy
    scraping_status['is_running'] = True
    
    response = client.post('/update-analysis', json={})
    
    assert response.status_code == 409
    assert response.is_json
    
    data = response.get_json()
    assert data == {'busy': True}


@pytest.mark.buttons
def test_pull_data_triggers_background_process(client, fake_scraper, mock_psycopg_connect):
    """Test that pull-data endpoint triggers background processing"""
    # Ensure not busy initially
    scraping_status['is_running'] = False
    
    # Mock the threading to execute immediately (synchronously)
    with patch('flask_app.threading.Thread') as MockThread:
        # Create a mock thread instance
        mock_thread_instance = MagicMock()
        
        # Make thread execution synchronous
        def mock_thread_start():
            # Execute the target function immediately
            mock_thread_instance.target(*mock_thread_instance.args, **mock_thread_instance.kwargs)
            # Ensure scraper state is updated immediately
            fake_scraper.scraped = True
            scraping_status['is_running'] = False
        
        mock_thread_instance.start = mock_thread_start
        MockThread.return_value = mock_thread_instance
        
        # Make the request
        response = client.post('/pull-data', json={})
        
        assert response.status_code == 202
        data = response.get_json()
        assert data == {'ok': True}
        
        # State is immediately observable (no polling needed)
        assert fake_scraper.scraped == True, "Fake scraper should have been called"
        assert scraping_status['is_running'] == False, "Scraping should be complete"


@pytest.mark.buttons
def test_pull_data_with_failing_scraper(client, fake_failing_scraper, mock_psycopg_connect):
    """Test pull-data endpoint handles scraper failures gracefully"""
    # Create app with failing scraper
    from tests.conftest import MockGradCafeQueryAnalyzer
    from flask_app import create_app
    
    # Mock threading for synchronous execution
    with patch('flask_app.threading.Thread') as MockThread:
        def mock_thread_init(target=None, args=None, kwargs=None):
            mock_instance = MagicMock()
            mock_instance.target = target
            mock_instance.args = args or ()
            mock_instance.kwargs = kwargs or {}
            
            def mock_start():
                # Execute the target function immediately and capture any errors
                try:
                    mock_instance.target(*mock_instance.args, **mock_instance.kwargs)
                except Exception as e:
                    pass  # The error will be handled by the target function itself
            
            mock_instance.start = mock_start
            return mock_instance
        
        MockThread.side_effect = mock_thread_init
        
        with patch('flask_app.GradCafeQueryAnalyzer', MockGradCafeQueryAnalyzer):
            app = create_app(
                config={'TESTING': True},
                db_config={'host': 'test', 'port': 5432, 'dbname': 'test', 'user': 'test', 'password': ''},
                scraper=fake_failing_scraper
            )
            test_client = app.test_client()
        
        # Reset status
        scraping_status['is_running'] = False
        scraping_status['error'] = None
        
        response = test_client.post('/pull-data', json={})
        
        assert response.status_code == 202
        data = response.get_json()
        assert data == {'ok': True}
        
        # Error state is immediately observable (no polling needed)
        assert scraping_status['is_running'] == False
        assert scraping_status['error'] is not None
        assert 'Test scraping failure' in scraping_status['error']


@pytest.mark.buttons
def test_concurrent_pull_data_requests(client, fake_scraper, mock_psycopg_connect):
    """Test that concurrent pull-data requests are handled correctly"""
    # First request
    scraping_status['is_running'] = False
    response1 = client.post('/pull-data', json={})
    assert response1.status_code == 202
    
    # Set as running to simulate first request in progress
    scraping_status['is_running'] = True
    
    # Second request should be rejected with busy status
    response2 = client.post('/pull-data', json={})
    assert response2.status_code == 409
    data2 = response2.get_json()
    assert data2 == {'busy': True}


@pytest.mark.buttons
def test_concurrent_update_analysis_requests(client, fake_scraper, mock_psycopg_connect):
    """Test that update-analysis is blocked during pull-data"""
    # Set as running (simulating pull-data in progress)
    scraping_status['is_running'] = True
    
    response = client.post('/update-analysis', json={})
    assert response.status_code == 409
    data = response.get_json()
    assert data == {'busy': True}


@pytest.mark.buttons
def test_button_endpoints_accept_json_content_type(client, mock_psycopg_connect):
    """Test that endpoints accept JSON content type"""
    scraping_status['is_running'] = False
    scraping_status['error'] = None
    
    # Test with explicit JSON content type
    response = client.post('/pull-data', 
                          data=json.dumps({}),
                          content_type='application/json')
    assert response.status_code == 202
    
    # Reset status again before second request
    scraping_status['is_running'] = False
    
    response = client.post('/update-analysis',
                          data=json.dumps({}), 
                          content_type='application/json')
    assert response.status_code == 200


@pytest.mark.buttons
def test_button_endpoints_without_json_body(client, mock_psycopg_connect):
    """Test that endpoints work without JSON body"""
    scraping_status['is_running'] = False
    
    # Test without JSON body
    response = client.post('/pull-data')
    assert response.status_code == 202
    
    # Reset status after pull-data (since it starts a background thread)
    scraping_status['is_running'] = False
    
    response = client.post('/update-analysis')
    assert response.status_code == 200


@pytest.mark.buttons
def test_pull_data_endpoint_method_restrictions(client, mock_psycopg_connect):
    """Test that pull-data endpoint only accepts POST requests"""
    # GET should not be allowed
    response = client.get('/pull-data')
    assert response.status_code == 405  # Method Not Allowed
    
    # PUT should not be allowed
    response = client.put('/pull-data')
    assert response.status_code == 405


@pytest.mark.buttons
def test_update_analysis_endpoint_method_restrictions(client, mock_psycopg_connect):
    """Test that update-analysis endpoint only accepts POST requests"""
    # GET should not be allowed
    response = client.get('/update-analysis')
    assert response.status_code == 405  # Method Not Allowed
    
    # PUT should not be allowed
    response = client.put('/update-analysis')
    assert response.status_code == 405


@pytest.mark.buttons
def test_status_endpoint_reflects_scraping_state(client, mock_psycopg_connect):
    """Test that status endpoint reflects current scraping state"""
    # Test when not running
    scraping_status['is_running'] = False
    scraping_status['progress'] = 'Idle'
    scraping_status['error'] = None
    
    response = client.get('/status')
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['is_running'] == False
    assert data['progress'] == 'Idle'
    assert data['error'] is None
    
    # Test when running
    scraping_status['is_running'] = True
    scraping_status['progress'] = 'Processing...'
    
    response = client.get('/status')
    data = response.get_json()
    
    assert data['is_running'] == True
    assert data['progress'] == 'Processing...'
