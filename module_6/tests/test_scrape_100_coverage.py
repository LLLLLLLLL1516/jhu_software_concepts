"""
Targeted tests to achieve 100% coverage for scrape.py
Specifically targets the 13 uncovered lines
"""
# pylint: disable=duplicate-code

import os
import sys
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# pylint: disable=import-error,wrong-import-position
from scrape import GradCafeListScraper
# pylint: enable=import-error,wrong-import-position
# pylint: disable=protected-access


class TestTargeted100Coverage:
    """Targeted tests for 100% coverage"""

    @pytest.mark.analysis
    def test_line_108_semester_match_found(self):
        """Test line 108 - return semester_match.group(0)"""
        with patch.object(GradCafeListScraper, "_check_robots_txt", return_value=True):
            scraper = GradCafeListScraper()

            # Create HTML with semester in text content (not in badges)
            html = "<tr><td>Applied for Fall 2025 semester</td></tr>"
            soup = BeautifulSoup(html, "html.parser")
            row = soup.find("tr")

            # This should find the semester in text and return it at line 108
            result = scraper._extract_semester(row)
            assert result == "Fall 2025"

    @pytest.mark.analysis
    def test_line_133_status_capitalize(self):
        """Test line 133 - status.capitalize() for non-waitlisted status"""
        with patch.object(GradCafeListScraper, "_check_robots_txt", return_value=True):
            scraper = GradCafeListScraper()

            # Create HTML with "Accepted on" pattern (not waitlisted)
            html = "<tr><td>Accepted on 15 Mar</td></tr>"
            soup = BeautifulSoup(html, "html.parser")
            row = soup.find("tr")

            status_info = scraper._extract_status_info(row)
            assert status_info["status"] == "Accepted"
            assert status_info["status_date"] == "15 Mar"

    @pytest.mark.analysis
    def test_lines_191_195_program_creation(self):
        """Test lines 191, 195 - program field creation"""
        with patch.object(GradCafeListScraper, "_check_robots_txt", return_value=True):
            scraper = GradCafeListScraper()

            # Test line 191 - program = major when major exists but school is empty
            html1 = """
            <tr>
                <td></td>
                <td><div class="tw-text-gray-900"><span>Computer Science</span></div></td>
                <td>2025-03-15</td>
                <td>Accepted</td>
            </tr>
            """
            soup1 = BeautifulSoup(html1, "html.parser")
            row1 = soup1.find("tr")
            result1 = scraper._parse_list_entry(row1)
            # Should have major and create program = major at line 191 (no school)
            assert result1 is not None
            assert result1["major"] == "Computer Science"
            assert result1["school"] == ""
            assert result1["program"] == "Computer Science"  # Line 191: program = major

            # Test line 195 - program = None when both major and school are None/empty
            html2 = """
            <tr>
                <td></td>
                <td><div class="tw-text-gray-900"><span></span></div></td>
                <td>2025-03-15</td>
                <td>Accepted</td>
            </tr>
            """
            soup2 = BeautifulSoup(html2, "html.parser")
            row2 = soup2.find("tr")
            result2 = scraper._parse_list_entry(row2)
            # Should set program = None at line 195
            assert result2 is not None
            assert result2["major"] == ""
            assert result2["school"] == ""
            assert result2["program"] is None  # Line 195: program = None

    @pytest.mark.analysis
    def test_lines_220_221_status_without_date(self):
        """Test lines 220-221 - status without date pattern"""
        with patch.object(GradCafeListScraper, "_check_robots_txt", return_value=True):
            scraper = GradCafeListScraper()

            # Create row with status text but no "on" pattern
            html = """
            <tr>
                <td>MIT</td>
                <td><div class="tw-text-gray-900"><span>CS</span></div></td>
                <td>2025-03-15</td>
                <td><div class="tw-inline-flex tw-items-center">Accepted</div></td>
            </tr>
            """
            soup = BeautifulSoup(html, "html.parser")
            row = soup.find("tr")

            result = scraper._parse_list_entry(row)
            # Should set status without date at lines 220-221
            assert result is not None
            assert result["status"] == "Accepted"
            assert result["status_date"] is None

    @pytest.mark.web
    def test_lines_380_383_pagination_links(self):
        """Test lines 380-383 - pagination with numbered links"""
        with patch.object(GradCafeListScraper, "_check_robots_txt", return_value=True):
            scraper = GradCafeListScraper()

            # Create HTML with pagination div containing numbered links
            html = """
            <html>
            <body>
                <div class="pagination">
                    <a>Previous</a>
                    <a>1</a>
                    <a>2</a>
                    <a>3</a>
                    <a>25</a>
                    <a>Next</a>
                </div>
            </body>
            </html>
            """

            with patch.object(scraper, "_make_request", return_value=html):
                total_pages = scraper._get_total_pages()
                # Should find page links and return max (25) at lines 380-383
                assert total_pages == 25

    @pytest.mark.integration
    def test_lines_456_460_461_progress_and_save(self):
        """Test lines 456, 460-461 - progress print and intermediate save"""
        with patch.object(GradCafeListScraper, "_check_robots_txt", return_value=True):
            scraper = GradCafeListScraper()

            # Create sample HTML with results
            html = """
            <table class="tw-min-w-full">
                <tbody>
                    <tr>
                        <td>MIT</td>
                        <td><div class="tw-text-gray-900"><span>CS</span></div></td>
                        <td>2025-03-15</td>
                        <td>Accepted</td>
                    </tr>
                </tbody>
            </table>
            """

            with patch("time.sleep"):
                with patch.object(scraper, "_make_request", return_value=html):
                    with patch.object(scraper, "_get_total_pages", return_value=60):
                        with patch.object(scraper, "save_data") as mock_save:
                            with patch("builtins.print") as mock_print:
                                # Scrape 60 pages to trigger progress at page 10 and save at page 50
                                _ = scraper.scrape_data(max_pages=60, target_entries=1000)

                                # Should have printed progress at page 10, 20, 30, 40, 50
                                progress_calls = [
                                    call
                                    for call in mock_print.call_args_list
                                    if "Progress:" in str(call)
                                ]
                                assert len(progress_calls) > 0

                                # Should have saved intermediate results at page 50
                                save_calls = [
                                    call
                                    for call in mock_save.call_args_list
                                    if "partial_50" in str(call)
                                ]
                                assert len(save_calls) == 1
