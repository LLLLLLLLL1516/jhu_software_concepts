#!/usr/bin/env python3
"""
List view scraper for Grad Cafe data
Scrapes graduate school admission results from thegradcafe.com list view
This approach is more efficient than scraping individual detail pages
"""

import json
import re
import time
import urllib3
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import urllib.robotparser


class GradCafeListScraper:
    """Web scraper for Grad Cafe admission results using list view"""
    
    def __init__(self, email: str = "wliu125@jh.edu"):
        self.http = urllib3.PoolManager()
        self.base_url = "https://www.thegradcafe.com"
        self.results_url = "https://www.thegradcafe.com/survey/index.php"
        self.scraped_data = []
        self.email = email
        self.user_agent = f"Academic Research Bot (+{email})"
        
        # Check robots.txt compliance
        self._check_robots_txt()
        
    def _check_robots_txt(self) -> bool:
        """Check robots.txt compliance programmatically"""
        try:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{self.base_url}/robots.txt")
            rp.read()
            
            can_fetch = rp.can_fetch(self.user_agent, self.results_url)
            print(f"Robots.txt check: {'ALLOWED' if can_fetch else 'DISALLOWED'}")
            
            if not can_fetch:
                print("WARNING: robots.txt disallows scraping this URL")
                return False
            return True
            
        except Exception as e:
            print(f"Could not check robots.txt: {e}")
            print("Proceeding with caution...")
            return True
    
    def _make_request(self, url: str, params: Optional[Dict] = None, retry_count: int = 3) -> Optional[str]:
        """Make HTTP request with error handling, rate limiting, and retries"""
        if params:
            query_string = urlencode(params)
            url = f"{url}?{query_string}"
        
        for attempt in range(retry_count):
            try:
                response = self.http.request(
                    'GET', url, 
                    headers={'User-Agent': self.user_agent},
                    timeout=30.0
                )
                
                if response.status == 200:
                    return response.data.decode('utf-8')
                elif response.status == 429:  # Rate limited
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status >= 500:  # Server error
                    wait_time = 2 ** attempt
                    print(f"Server error {response.status}, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"HTTP {response.status} error for URL: {url}")
                    return None
                    
            except Exception as e:
                wait_time = 2 ** attempt
                print(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return None
        
        return None
    
    def _extract_semester(self, row_element) -> Optional[str]:
        """Extract semester/year from badge elements (e.g., Fall 2026, Spring 2026)"""
        # Look for semester badges (usually orange/colored badges)
        badges = row_element.find_all(['span', 'div'], class_=re.compile(r'badge|label|tag', re.I))
        
        for badge in badges:
            text = badge.get_text(strip=True)
            # Match patterns like "Fall 2026", "Spring 2025", etc.
            if re.match(r'^(Fall|Spring|Summer|Winter)\s+\d{4}$', text, re.I):
                return text
        
        # Alternative: Look in text content
        text_content = row_element.get_text()
        semester_match = re.search(r'\b(Fall|Spring|Summer|Winter)\s+\d{4}\b', text_content, re.I)
        if semester_match:
            return semester_match.group(0)
        
        return None
    
    def _extract_status_info(self, row_element) -> Dict[str, Optional[str]]:
        """Extract acceptance status and date"""
        status_info = {
            'status': None,
            'status_date': None
        }
        
        # Look for status text patterns
        text = row_element.get_text()
        
        # Pattern: "Accepted on 1 Sep", "Rejected on 2 Sep", "Interview on 15 Mar", "Wait listed on 6 Feb"
        # Handle both "Waitlisted" and "Wait listed" (with space)
        status_pattern = r'(Accepted|Rejected|Interview|Wait\s*listed|Waitlisted)\s+on\s+(\d{1,2}\s+\w+)'
        match = re.search(status_pattern, text, re.I)
        
        if match:
            # Normalize "Wait listed" to "Waitlisted" for consistency
            status = match.group(1)
            if 'wait' in status.lower():
                status_info['status'] = 'Waitlisted'
            else:
                status_info['status'] = status.capitalize()
            status_info['status_date'] = match.group(2)
        else:
            # Look for status in specific elements
            for elem in row_element.find_all(['span', 'div', 'td']):
                elem_text = elem.get_text(strip=True)
                # Handle both "Waitlisted" and "Wait listed"
                if re.match(r'^(Accepted|Rejected|Interview|Wait\s*listed|Waitlisted)$', elem_text, re.I):
                    # Normalize "Wait listed" to "Waitlisted"
                    if 'wait' in elem_text.lower():
                        status_info['status'] = 'Waitlisted'
                    else:
                        status_info['status'] = elem_text.capitalize()
                    break
        
        return status_info
    
    def _extract_scores(self, row_element) -> Dict[str, Optional[str]]:
        """Extract GPA and GRE scores from the row"""
        scores = {
            'gpa': None,
            'gre_total': None,
            'gre_verbal': None,
            'gre_quant': None,
            'gre_aw': None
        }
        
        text = row_element.get_text()
        
        # Extract GPA (e.g., "GPA 3.22", "GPA: 3.90")
        gpa_match = re.search(r'GPA\s*:?\s*(\d+\.\d+)', text, re.I)
        if gpa_match:
            scores['gpa'] = gpa_match.group(1)
        
        # Extract GRE Total (e.g., "GRE 331", "GRE: 320")
        gre_total_match = re.search(r'GRE\s*:?\s*(\d{3})\b', text, re.I)
        if gre_total_match:
            scores['gre_total'] = gre_total_match.group(1)
        
        # Extract GRE Verbal (e.g., "GRE V 165", "V: 160")
        gre_v_match = re.search(r'(?:GRE\s*)?V(?:erbal)?\s*:?\s*(\d{3})\b', text, re.I)
        if gre_v_match:
            scores['gre_verbal'] = gre_v_match.group(1)
        
        # Extract GRE Quant (e.g., "GRE Q 170", "Q: 165")
        gre_q_match = re.search(r'(?:GRE\s*)?Q(?:uant)?\s*:?\s*(\d{3})\b', text, re.I)
        if gre_q_match:
            scores['gre_quant'] = gre_q_match.group(1)
        
        # Extract GRE AW (e.g., "GRE AW 4.5", "AW: 5.0")
        gre_aw_match = re.search(r'(?:GRE\s*)?AW\s*:?\s*(\d+(?:\.\d+)?)\b', text, re.I)
        if gre_aw_match:
            scores['gre_aw'] = gre_aw_match.group(1)
        
        return scores
    
    def _parse_list_entry(self, main_row, detail_row=None, comment_row=None) -> Optional[Dict[str, Any]]:
        """Parse a complete entry from the list view (main row + detail row + optional comment)"""
        try:
            result = {}
            
            # Parse main row
            cells = main_row.find_all('td')
            if len(cells) < 4:
                return None
            
            # Extract school (first column)
            school_cell = cells[0]
            result['school'] = school_cell.get_text(strip=True)
            
            # Extract major and degree (second column)
            program_cell = cells[1]
            program_div = program_cell.find('div', class_='tw-text-gray-900')
            if program_div:
                # Major and degree are separated by a bullet point
                spans = program_div.find_all('span')
                if spans:
                    result['major'] = spans[0].get_text(strip=True)
                    if len(spans) > 1:
                        # The last span usually contains the degree
                        degree_text = spans[-1].get_text(strip=True)
                        result['degree'] = degree_text
                    else:
                        result['degree'] = None
                else:
                    result['major'] = None
            else:
                result['major'] = None
            
            # Create combined program field (major, school) for downstream compatibility
            school = result.get('school', '').strip()
            major = result.get('major', '').strip()
            
            if major and school:
                result['program'] = f"{major}, {school}"
            elif major:
                result['program'] = major
            elif school:
                result['program'] = school
            else:
                result['program'] = None
            
            # Extract date added (third column on desktop, may be hidden on mobile)
            if len(cells) > 2:
                date_cell = cells[2]
                result['date_added'] = date_cell.get_text(strip=True)
            
            # Extract status from fourth column (desktop) or from detail row badges
            if len(cells) > 3:
                status_cell = cells[3]
                status_div = status_cell.find('div', class_=re.compile(r'tw-inline-flex.*tw-items-center'))
                if status_div:
                    status_text = status_div.get_text(strip=True)
                    # Parse status like "Accepted on 1 Sep" or "Wait listed on 6 Feb"
                    # Handle both "Waitlisted" and "Wait listed" (with space)
                    status_match = re.match(r'(Accepted|Rejected|Interview|Wait\s*listed|Waitlisted)\s+on\s+(.+)', status_text, re.I)
                    if status_match:
                        # Normalize "Wait listed" to "Waitlisted" for consistency
                        status = status_match.group(1)
                        if 'wait' in status.lower():
                            result['status'] = 'Waitlisted'
                        else:
                            result['status'] = status.capitalize()
                        result['status_date'] = status_match.group(2)
                    else:
                        result['status'] = status_text
                        result['status_date'] = None
            
            # Extract URL from the comment/options links
            link = main_row.find('a', href=re.compile(r'/result/\d+'))
            if link:
                result['url'] = self.base_url + link.get('href')
            
            # Parse detail row if available
            if detail_row:
                # Extract badges from detail row
                badges = detail_row.find_all('div', class_=re.compile(r'tw-inline-flex.*tw-items-center.*tw-rounded-md'))
                
                for badge in badges:
                    badge_text = badge.get_text(strip=True)
                    
                    # Extract semester (Fall/Spring + Year)
                    if re.match(r'^(Fall|Spring|Summer|Winter)\s+\d{4}$', badge_text, re.I):
                        result['semester'] = badge_text
                    
                    # Extract applicant type
                    elif badge_text.lower() in ['international', 'american', 'domestic', 'us']:
                        result['applicant_type'] = badge_text.capitalize()
                    
                    # Extract GPA
                    elif badge_text.startswith('GPA'):
                        gpa_match = re.search(r'GPA\s*(\d+\.\d+)', badge_text)
                        if gpa_match:
                            result['gpa'] = gpa_match.group(1)
                    
                    # Extract GRE scores
                    elif 'GRE' in badge_text:
                        if badge_text.startswith('GRE V'):
                            gre_v_match = re.search(r'GRE V\s*(\d+)', badge_text)
                            if gre_v_match:
                                result['gre_verbal'] = gre_v_match.group(1)
                        elif badge_text.startswith('GRE Q'):
                            gre_q_match = re.search(r'GRE Q\s*(\d+)', badge_text)
                            if gre_q_match:
                                result['gre_quant'] = gre_q_match.group(1)
                        elif badge_text.startswith('GRE AW'):
                            gre_aw_match = re.search(r'GRE AW\s*(\d+(?:\.\d+)?)', badge_text)
                            if gre_aw_match:
                                result['gre_aw'] = gre_aw_match.group(1)
                        elif badge_text.startswith('GRE'):
                            # This is likely the total GRE score
                            gre_match = re.search(r'GRE\s*(\d+)', badge_text)
                            if gre_match:
                                result['gre_total'] = gre_match.group(1)
            
            # Parse comment row if available
            if comment_row:
                comment_p = comment_row.find('p', class_='tw-text-gray-500')
                if comment_p:
                    result['comments'] = comment_p.get_text(strip=True)
            
            # Set defaults for missing fields
            if 'semester' not in result:
                result['semester'] = None
            if 'applicant_type' not in result:
                result['applicant_type'] = None
            if 'gpa' not in result:
                result['gpa'] = None
            if 'gre_total' not in result:
                result['gre_total'] = None
            if 'gre_verbal' not in result:
                result['gre_verbal'] = None
            if 'gre_quant' not in result:
                result['gre_quant'] = None
            if 'gre_aw' not in result:
                result['gre_aw'] = None
            if 'comments' not in result:
                result['comments'] = None
            
            return result
            
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None
    
    def _parse_list_page(self, html: str) -> List[Dict[str, Any]]:
        """Parse a list page and extract all admission results"""
        soup = BeautifulSoup(html, "html.parser")
        results = []
        
        # Find the main results table
        table = soup.find('table', class_='tw-min-w-full')
        if not table:
            # Try finding any table
            tables = soup.find_all('table')
            table = tables[0] if tables else None
        
        if not table:
            print("No table found on page")
            return results
        
        # Find the tbody
        tbody = table.find('tbody')
        if not tbody:
            tbody = table  # Fallback to table itself
        
        # Get all rows
        rows = tbody.find_all('tr')
        
        # Process rows - they come in groups (main row, detail row, optional comment row)
        i = 0
        while i < len(rows):
            row = rows[i]
            
            # Skip if this is a header row
            if row.find('th') and not row.find('td'):
                i += 1
                continue
            
            # Check if this is a main data row (has multiple td elements)
            cells = row.find_all('td')
            if len(cells) >= 4:  # Main row has at least 4 cells
                main_row = row
                detail_row = None
                comment_row = None
                
                # Check if next row is a detail row (has badges)
                if i + 1 < len(rows):
                    next_row = rows[i + 1]
                    # Detail rows typically have class "tw-border-none" and contain badges
                    if 'tw-border-none' in next_row.get('class', []):
                        detail_row = next_row
                        i += 1
                        
                        # Check if there's a comment row after the detail row
                        if i + 1 < len(rows):
                            potential_comment = rows[i + 1]
                            if 'tw-border-none' in potential_comment.get('class', []):
                                # Check if it contains a comment paragraph
                                if potential_comment.find('p', class_='tw-text-gray-500'):
                                    comment_row = potential_comment
                                    i += 1
                
                # Parse the complete entry
                result = self._parse_list_entry(main_row, detail_row, comment_row)
                if result and result.get('school'):
                    results.append(result)
            
            i += 1
        
        return results
    
    def _get_total_pages(self) -> int:
        """Determine the total number of pages available"""
        try:
            html = self._make_request(self.results_url)
            if not html:
                return 1
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for pagination elements
            pagination = soup.find(['div', 'nav', 'ul'], class_=re.compile(r'paginat', re.I))
            if pagination:
                # Find all page numbers
                page_links = pagination.find_all('a', string=re.compile(r'^\d+$'))
                if page_links:
                    page_numbers = [int(link.get_text()) for link in page_links]
                    return max(page_numbers)
            
            # Alternative: Look for "Page X of Y" text
            page_text = soup.get_text()
            match = re.search(r'Page\s+\d+\s+of\s+(\d+)', page_text, re.I)
            if match:
                return int(match.group(1))
            
            # Default fallback
            return 1000
            
        except Exception as e:
            print(f"Could not determine total pages: {e}")
            return 1000
    
    def scrape_data(self, max_pages: int = None, target_entries: int = 30000) -> List[Dict[str, Any]]:
        """
        Main scraping method to collect grad cafe data from list view
        
        Args:
            max_pages: Maximum number of pages to scrape (None for auto-detect)
            target_entries: Target number of entries to collect
            
        Returns:
            List of scraped admission results
        """
        print("Starting Grad Cafe list view scraping...")
        print(f"Target: {target_entries} entries")
        
        if max_pages is None:
            max_pages = min(self._get_total_pages(), 1500)
            print(f"Detected max pages: {max_pages}")
        
        all_results = []
        page = 1
        consecutive_empty_pages = 0
        
        while page <= max_pages and len(all_results) < target_entries:
            print(f"Scraping page {page}/{max_pages}...")
            
            # Make request with page parameter
            params = {'page': str(page)} if page > 1 else {}
            html = self._make_request(self.results_url, params)
            
            if not html:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 5:
                    print("Too many consecutive empty pages, stopping.")
                    break
                page += 1
                continue
            
            # Parse the page
            page_results = self._parse_list_page(html)
            
            if not page_results:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 5:
                    print("Too many consecutive empty pages, stopping.")
                    break
            else:
                consecutive_empty_pages = 0
                all_results.extend(page_results)
                print(f"  Found {len(page_results)} results on page {page}")
                print(f"  Total entries collected: {len(all_results)}")
            
            # Rate limiting
            time.sleep(1.5)  # Be respectful to the server
            
            page += 1
            
            # Progress update every 10 pages
            if page % 10 == 0:
                print(f"Progress: {len(all_results)} entries from {page} pages")
            
            # Save intermediate results every 50 pages
            if page % 50 == 0:
                self.scraped_data = all_results
                self.save_data(f"applicant_data_list_partial_{page}.json")
        
        self.scraped_data = all_results
        print(f"Scraping completed. Total entries: {len(all_results)}")
        return all_results
    
    def save_data(self, filename: str = "applicant_data_list.json") -> None:
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def load_data(self, filename: str = "applicant_data_list.json") -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.scraped_data = json.load(f)
            print(f"Data loaded from {filename}: {len(self.scraped_data)} entries")
            return self.scraped_data
        except Exception as e:
            print(f"Error loading data: {e}")
            return []


def main():
    """Main function to run the list view scraper"""
    # Initialize scraper with proper email for identification
    scraper = GradCafeListScraper(email="wei.liu@jh.edu")
    
    print("=" * 60)
    print("Grad Cafe List View Scraper")
    print("=" * 60)

    # Start with a small test to verify the approach works
    print("\nStarting with a small test (2 pages)...")
    test_results = scraper.scrape_data(max_pages=2, target_entries=50)
    
    if test_results:
        print(f"\nTest successful! Found {len(test_results)} results.")
        print("\nSample results:")
        
        # Show semester data specifically
        semesters = [r.get('semester') for r in test_results if r.get('semester')]
        if semesters:
            print(f"\nSemester data found: {set(semesters)}")
        
        print(f"\nTest completed successfully.")
        print("To scrape more data, increase max_pages parameter.")
        print("For 30,000 entries, you'll need approximately 1,500 pages.")
    else:
        print("Test failed - no results found. Please check the website structure.")
    
    # Save test results
    scraper.save_data("applicant_data_list_test.json")

    # For production
    # results = scraper.scrape_data(max_pages=1500, target_entries=30000)
    # scraper.save_data("applicant_data_full.json")


if __name__ == "__main__":
    main()
