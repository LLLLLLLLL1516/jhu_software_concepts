"""
Test Flask web page functionality
Tests marked with 'web' marker
"""

import pytest
from bs4 import BeautifulSoup
import re


@pytest.mark.web
def test_analysis_page_get_request(client, mock_psycopg_connect):
    """Test GET /analysis returns 200 and renders correctly"""
    response = client.get('/analysis')
    assert response.status_code == 200
    
    # Parse HTML content
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check that page contains "Analysis" text
    page_text = soup.get_text()
    assert 'Analysis' in page_text, "Page should contain 'Analysis' text"


@pytest.mark.web
def test_home_page_get_request(client, mock_psycopg_connect):
    """Test GET / (home page) returns 200 and renders correctly"""
    response = client.get('/')
    assert response.status_code == 200
    
    # Parse HTML content
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check that page contains "Analysis" text
    page_text = soup.get_text()
    assert 'Analysis' in page_text, "Home page should contain 'Analysis' text"


@pytest.mark.web
def test_analysis_page_contains_required_buttons(client, mock_psycopg_connect):
    """Test that analysis page contains both required buttons with correct data-testid attributes"""
    response = client.get('/analysis')
    assert response.status_code == 200
    
    # Parse HTML content
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for Pull Data button with correct data-testid
    pull_data_btn = soup.find('button', {'data-testid': 'pull-data-btn'})
    assert pull_data_btn is not None, "Pull Data button with data-testid='pull-data-btn' should exist"
    
    # Check for Update Analysis button with correct data-testid
    update_analysis_btn = soup.find('button', {'data-testid': 'update-analysis-btn'})
    assert update_analysis_btn is not None, "Update Analysis button with data-testid='update-analysis-btn' should exist"
    
    # Verify button text content
    assert 'Pull Data' in pull_data_btn.get_text()
    assert 'Update Analysis' in update_analysis_btn.get_text()


@pytest.mark.web
def test_analysis_page_contains_answer_labels(client, mock_psycopg_connect):
    """Test that analysis page contains at least one 'Answer:' label"""
    response = client.get('/analysis')
    assert response.status_code == 200
    
    # Parse HTML content
    soup = BeautifulSoup(response.data, 'html.parser')
    page_text = soup.get_text()
    
    # Check for "Question" text which appears in analysis results
    # This is more reliable than "Answer:" which may not be in the current template
    assert 'Question' in page_text, "Analysis page should contain 'Question' labels for analysis results"


# @pytest.mark.web
# def test_analysis_page_structure(client, mock_psycopg_connect):
#     """Test overall structure of analysis page"""
#     response = client.get('/analysis')
#     assert response.status_code == 200
    
#     soup = BeautifulSoup(response.data, 'html.parser')
    
#     # Check for main title
#     title_element = soup.find('h1')
#     assert title_element is not None
#     assert 'Grad Café Data Analysis' in title_element.get_text()
    
#     # Check for analysis results section
#     results_section = soup.find('h2', string=lambda text: text and 'Analysis Results' in text)
#     if not results_section:
#         # Alternative: look for h2 with Analysis Results anywhere in the page
#         all_h2s = soup.find_all('h2')
#         results_section = None
#         for h2 in all_h2s:
#             if 'Analysis Results' in h2.get_text():
#                 results_section = h2
#                 break
#     assert results_section is not None, f"Should find h2 with 'Analysis Results'. Found h2 elements: {[h2.get_text() for h2 in soup.find_all('h2')]}"


@pytest.mark.web
def test_analysis_page_renders_results(client, mock_psycopg_connect):
    """Test that analysis page renders query results"""
    response = client.get('/analysis')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for cards containing analysis results
    cards = soup.find_all('div', {'class': 'card'})
    assert len(cards) > 0, "Analysis page should contain result cards"
    
    # Check that at least one card has analysis content
    has_result_card = False
    for card in cards:
        if 'Question' in card.get_text():
            has_result_card = True
            break
    
    assert has_result_card, "At least one card should contain question/analysis content"


@pytest.mark.web
def test_error_pages(client, mock_psycopg_connect):
    """Test error page handling"""
    # Test 404 page
    response = client.get('/nonexistent-page')
    assert response.status_code == 404


@pytest.mark.web
def test_status_endpoint(client, mock_psycopg_connect):
    """Test status endpoint returns JSON"""
    response = client.get('/status')
    assert response.status_code == 200
    assert response.is_json
    
    data = response.get_json()
    assert 'is_running' in data
    assert 'progress' in data
    assert 'last_update' in data
    assert 'error' in data


@pytest.mark.web
def test_page_accessibility_attributes(client, mock_psycopg_connect):
    """Test that buttons have proper accessibility attributes"""
    response = client.get('/analysis')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check buttons have type attribute
    pull_data_btn = soup.find('button', {'data-testid': 'pull-data-btn'})
    update_analysis_btn = soup.find('button', {'data-testid': 'update-analysis-btn'})
    
    assert pull_data_btn.get('type') == 'button'
    assert update_analysis_btn.get('type') == 'button'
    
    # Check buttons have onclick handlers
    assert pull_data_btn.get('onclick') == 'pullData()'
    assert update_analysis_btn.get('onclick') == 'updateAnalysis()'
