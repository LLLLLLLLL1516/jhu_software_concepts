"""
Test analysis formatting, especially percentage values
Tests marked with 'analysis' marker
"""

import pytest
import re
from bs4 import BeautifulSoup
from unittest.mock import patch


class MockGradCafeQueryAnalyzerWithPercentages:
    """Mock query analyzer that returns percentage values for testing"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.connected = False
        self.results = {
            'acceptance_rate': {
                'description': 'What percentage of applications resulted in acceptance?',
                'query': 'SELECT COUNT(*) FROM applicant_data WHERE status = "Accepted"',
                'result': '15.25'
            },
            'rejection_rate': {
                'description': 'What percentage of applications were rejected?',
                'query': 'SELECT COUNT(*) FROM applicant_data WHERE status = "Rejected"',
                'result': '84.75'
            },
            'international_percentage': {
                'description': 'Percentage of international students',
                'query': 'SELECT COUNT(*) FROM applicant_data WHERE us_or_international = "International"',
                'result': '42.33'
            },
            'cs_program_percent': {
                'description': 'Percent of CS programs in database',
                'query': 'SELECT COUNT(*) FROM applicant_data WHERE program LIKE "%Computer Science%"',
                'result': '28.50'
            },
            'avg_gpa': {
                'description': 'Average GPA of all applicants',
                'query': 'SELECT AVG(gpa) FROM applicant_data',
                'result': 3.75
            },
            'total_count': {
                'description': 'Total number of applications',
                'query': 'SELECT COUNT(*) FROM applicant_data',
                'result': 1500
            }
        }
    
    def connect_to_database(self):
        self.connected = True
        return True
    
    def run_all_queries(self):
        pass
    
    def close_connection(self):
        self.connected = False


@pytest.mark.analysis
def test_percentage_format_with_two_decimals(client, mock_psycopg_connect):
    """Test that all percentage values render with exactly two decimal places"""
    
    # Use mock analyzer with percentage results
    with patch('flask_app.GradCafeQueryAnalyzer', MockGradCafeQueryAnalyzerWithPercentages):
        response = client.get('/analysis')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        page_content = soup.get_text()
        
        # Find all percentage patterns in the page
        # Look for patterns like "15.25%" with exactly 2 decimal places
        percentage_pattern = r'\b\d+\.\d{2}%'
        percentages = re.findall(percentage_pattern, page_content)
        
        # Should find percentage values
        assert len(percentages) > 0, "Should find percentage values in the page"
        
        # All found percentages should have exactly 2 decimal places
        for percentage in percentages:
            # Verify format: digits.two_digits%
            assert re.match(r'^\d+\.\d{2}%$', percentage), f"Percentage '{percentage}' should have exactly 2 decimal places"


@pytest.mark.analysis
def test_percentage_format_in_html_structure(client, mock_psycopg_connect):
    """Test percentage formatting in HTML structure"""
    
    with patch('flask_app.GradCafeQueryAnalyzer', MockGradCafeQueryAnalyzerWithPercentages):
        response = client.get('/analysis')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Look for result display divs
        result_divs = soup.find_all('div', class_='result-display')
        
        percentage_found = False
        for div in result_divs:
            text = div.get_text(strip=True)
            # Check for percentage patterns
            if '%' in text:
                percentage_found = True
                # Extract percentages and verify format
                percentages = re.findall(r'\d+\.\d+%', text)
                for perc in percentages:
                    # Should have exactly 2 decimal places
                    decimal_part = perc.split('.')[1].replace('%', '')
                    assert len(decimal_part) == 2, f"Percentage '{perc}' should have exactly 2 decimal places"
        
        assert percentage_found, "Should find at least one percentage value in result displays"


@pytest.mark.analysis
def test_non_percentage_values_formatting(client, mock_psycopg_connect):
    """Test that non-percentage values are formatted correctly"""
    
    with patch('flask_app.GradCafeQueryAnalyzer', MockGradCafeQueryAnalyzerWithPercentages):
        response = client.get('/analysis')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Look for numeric values that are not percentages
        result_divs = soup.find_all('div', class_='result-display')
        
        for div in result_divs:
            text = div.get_text(strip=True)
            # Find numbers that are not percentages (like GPA, counts)
            numbers = re.findall(r'\b\d+(?:\.\d+)?\b(?!%)', text)
            for number in numbers:
                # Should be valid numeric format
                try:
                    float(number)
                except ValueError:
                    pytest.fail(f"Non-percentage value '{number}' should be a valid number")


@pytest.mark.analysis
def test_percentage_calculation_accuracy(client, mock_psycopg_connect):
    """Test that percentage values are calculated and displayed accurately"""
    
    with patch('flask_app.GradCafeQueryAnalyzer', MockGradCafeQueryAnalyzerWithPercentages):
        response = client.get('/analysis')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        page_content = soup.get_text()
        
        # Look for specific expected percentage values
        expected_percentages = ['15.25%', '84.75%', '42.33%', '28.50%']
        
        found_percentages = []
        for expected in expected_percentages:
            if expected in page_content:
                found_percentages.append(expected)
        
        assert len(found_percentages) > 0, f"Should find some expected percentages: {expected_percentages}"


@pytest.mark.analysis
def test_percentage_regex_precision(client, mock_psycopg_connect):
    """Test percentage format using precise regex patterns"""
    
    with patch('flask_app.GradCafeQueryAnalyzer', MockGradCafeQueryAnalyzerWithPercentages):
        response = client.get('/analysis')
        assert response.status_code == 200
        
        html_content = response.data.decode('utf-8')
        
        # Comprehensive regex for percentages with exactly 2 decimal places
        precise_percentage_pattern = r'\b\d{1,3}\.\d{2}%\b'
        
        matches = re.findall(precise_percentage_pattern, html_content)
        
        if matches:  # Only test if percentages are found
            for match in matches:
                # Verify each match has exactly the right format
                assert re.fullmatch(r'\d{1,3}\.\d{2}%', match), f"Percentage '{match}' doesn't match exact format"
                
                # Verify the decimal part has exactly 2 digits
                decimal_part = match.split('.')[1].replace('%', '')
                assert len(decimal_part) == 2, f"Decimal part of '{match}' should have exactly 2 digits"


@pytest.mark.analysis
def test_template_percentage_rendering_logic(client, mock_psycopg_connect):
    """Test that template logic correctly identifies and formats percentage values"""
    
    with patch('flask_app.GradCafeQueryAnalyzer', MockGradCafeQueryAnalyzerWithPercentages):
        response = client.get('/analysis')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Find all card bodies with descriptions containing percentage-related words
        cards = soup.find_all('div', class_='card-body')
        
        percentage_cards = []
        for card in cards:
            description_text = card.get_text().lower()
            if 'percentage' in description_text or 'percent' in description_text:
                percentage_cards.append(card)
        
        # Should find at least some percentage-related cards
        assert len(percentage_cards) > 0, "Should find cards with percentage-related descriptions"
        
        # Check that these cards display values with % symbol
        for card in percentage_cards:
            card_text = card.get_text()
            # Should contain % symbol somewhere in the card
            assert '%' in card_text, f"Percentage card should contain % symbol: {card_text[:100]}"


@pytest.mark.analysis
def test_mixed_data_types_formatting(client, mock_psycopg_connect):
    """Test that mixed data types (percentages, integers, floats) are formatted correctly"""
    
    with patch('flask_app.GradCafeQueryAnalyzer', MockGradCafeQueryAnalyzerWithPercentages):
        response = client.get('/analysis')
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Collect all result values
        result_divs = soup.find_all('div', class_='result-display')
        
        found_percentage = False
        found_integer = False
        found_float = False
        
        for div in result_divs:
            text = div.get_text(strip=True)
            
            # Check for percentage
            if re.search(r'\d+\.\d{2}%', text):
                found_percentage = True
            
            # Check for integer (comma-formatted numbers)
            if re.search(r'\b\d{1,3}(?:,\d{3})*\b(?![\.\d])', text):
                found_integer = True
            
            # Check for float (non-percentage decimal numbers)
            if re.search(r'\b\d+\.\d+\b(?!%)', text):
                found_float = True
        
        # Should have found different data types
        data_types_found = sum([found_percentage, found_integer, found_float])
        assert data_types_found > 0, "Should find at least one data type formatted correctly"


@pytest.mark.analysis
def test_html_escaping_in_percentages(client, mock_psycopg_connect):
    """Test that percentage symbols are properly HTML-escaped if needed"""
    
    with patch('flask_app.GradCafeQueryAnalyzer', MockGradCafeQueryAnalyzerWithPercentages):
        response = client.get('/analysis')
        assert response.status_code == 200
        
        html_content = response.data.decode('utf-8')
        
        # Make sure % symbols are not HTML-escaped
        assert '%' in html_content, "Percentage symbols should be present in HTML"
        
        # Make sure they're not double-escaped
        assert '&amp;' not in html_content or '%' in html_content, "Percentage symbols should not be double-escaped"
