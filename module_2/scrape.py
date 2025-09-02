#!/usr/bin/env python3
"""
Web scraper for Grad Cafe data
Scrapes graduate school admission results from thegradcafe.com
"""

import json
import re
import time
import urllib3
from urllib.parse import urlencode, urljoin
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import urllib.robotparser


class GradCafeScraper:
    """Web scraper for Grad Cafe admission results"""
    
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
    
    def _extract_detail_links(self, html: str) -> List[str]:
        """Extract detail page links from a list page"""
        soup = BeautifulSoup(html, "html.parser")
        links = []
        
        # Look for links that go to /result/<id>
        for a in soup.select('a[href^="/result/"]'):
            href = a.get("href")
            if not href:
                continue
            full_url = urljoin(self.base_url, href)
            if full_url not in links:
                links.append(full_url)
        
        return links
    
    def _is_valid_field_content(self, text: str, label: str) -> bool:
        """Validate that the extracted text is appropriate for the given field"""
        if not text or len(text.strip()) == 0:
            return False
        
        text = text.strip()
        label_lower = label.lower()
        
        # Filter out common UI elements and navigation text
        ui_elements = [
            'timeline', 'received notification', 'what do you think', 'content made to',
            'total reactions', 'see more', 'sign in', 'submit your results',
            'application information', 'acceptance rate'
        ]
        
        if any(ui_elem in text.lower() for ui_elem in ui_elements):
            return False
        
        # Filter out other field labels that might be picked up
        other_labels = [
            'institution', 'program', 'degree type', 'decision', 'notification',
            'undergrad gpa', 'gre general', 'gre verbal', 'gre quant', 'analytical writing',
            'notes', 'degree\'s country of origin'
        ]
        
        if text.lower() in [label.lower() for label in other_labels]:
            return False
        
        # Field-specific validation
        if 'gpa' in label_lower:
            # GPA should contain numbers and be reasonable
            return bool(re.search(r'\d', text)) and len(text) < 20
        
        elif 'gre' in label_lower:
            # GRE scores should be numeric or "0"
            return bool(re.match(r'^\d+(\.\d+)?$', text)) or text == '0'
        
        elif 'notes' in label_lower:
            # Notes should be substantial text, not short labels
            return len(text) > 5 and not text.lower().startswith(('gre', 'gpa'))
        
        elif 'notification' in label_lower:
            # Notification should contain date/method info
            return any(word in text.lower() for word in ['on', 'via', 'email', 'phone', 'website'])
        
        elif 'country' in label_lower:
            # Country field should be International, American, or similar
            return text.lower() in ['international', 'american', 'domestic', 'us']
        
        else:
            # For other fields, basic validation
            return len(text) < 200  # Reasonable length limit
    
    def _parse_detail_page(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Parse a detail page by looking for labeled fields using robust DOM structure parsing"""
        soup = BeautifulSoup(html, "html.parser")
        
        def extract_field_value(label_text: str) -> Optional[str]:
            """Extract field value using robust DOM structure parsing"""
            # Strategy 1: Look for dt/dd pattern (definition list structure)
            dt_element = soup.find('dt', string=re.compile(rf'^\s*{label_text}\s*$', re.I))
            if dt_element:
                # Look for the corresponding dd element
                dd_element = dt_element.find_next_sibling('dd')
                if dd_element:
                    text = dd_element.get_text(strip=True)
                    if text and self._is_valid_field_content(text, label_text):
                        return text
                    elif text:  # Return even if validation fails, for debugging
                        return text
            
            # Strategy 2: Look for label followed by colon and value pattern
            # This handles cases like "GRE General: 331" or "GRE Verbal: 165"
            pattern = rf'{re.escape(label_text)}\s*:\s*([^\n\r]+)'
            match = re.search(pattern, soup.get_text(), re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and self._is_valid_field_content(value, label_text):
                    return value
                elif value:  # Return even if validation fails, for debugging
                    return value
            
            # Strategy 3: Look for the label text and find nearby values
            label_element = soup.find(string=re.compile(rf'^\s*{label_text}\s*$', re.I))
            if label_element:
                # Get the parent container of the label
                label_parent = label_element.parent if hasattr(label_element, 'parent') else None
                if label_parent:
                    # Look for the next sibling element that contains the value
                    current = label_parent.next_sibling
                    attempts = 0
                    max_attempts = 5  # Limit search to prevent going too far
                    
                    while current and attempts < max_attempts:
                        if hasattr(current, 'get_text'):
                            text = current.get_text(strip=True)
                            if text and self._is_valid_field_content(text, label_text):
                                return text
                        elif isinstance(current, str):
                            text = current.strip()
                            if text and self._is_valid_field_content(text, label_text):
                                return text
                        
                        current = current.next_sibling
                        attempts += 1
            
            # Strategy 4: Look for text containing both label and value in same element
            # This handles cases where label and value are in the same text node
            all_text = soup.get_text()
            lines = all_text.split('\n')
            for line in lines:
                if label_text.lower() in line.lower() and ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        value = parts[1].strip()
                        if value and self._is_valid_field_content(value, label_text):
                            return value
                        elif value:  # Return even if validation fails
                            return value
            
            return None
        
        # Extract all the labeled fields from the detail page
        result = {
            "url": url,
            "school": extract_field_value("Institution"),
            "program": extract_field_value("Program"),
            "degree": extract_field_value("Degree Type"),
            "country_of_origin": extract_field_value("Degree's Country of Origin"),
            "status": extract_field_value("Decision"),
            "date_added": extract_field_value("Notification"),
            "GPA": extract_field_value("Undergrad GPA"),
            "GRE": extract_field_value("GRE General"),
            "GRE V": extract_field_value("GRE Verbal"),
            "GRE Q": extract_field_value("GRE Quant"),
            "GRE AW": extract_field_value("Analytical Writing"),
            "comments": extract_field_value("Notes"),
        }
        
        # Parse notification date if present (e.g., "on 11/02/2025 via E-mail")
        if result["date_added"]:
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', result["date_added"])
            if date_match:
                result["notification_date"] = date_match.group(1)
        
        # Create the combined program field as expected by LLM
        if result.get("school") and result.get("program"):
            result["program"] = f'{result["program"]}, {result["school"]}'
        elif result.get("school") and not result.get("program"):
            result["program"] = result["school"]
        
        # Map degree field to expected format
        if result.get("degree"):
            degree = result["degree"].lower()
            if "phd" in degree or "ph.d" in degree or "doctorate" in degree:
                result["Degree"] = "PhD"
            elif "master" in degree or "ms" in degree or "ma" in degree:
                result["Degree"] = "Masters"
            else:
                result["Degree"] = result["degree"]
        
        # Map other fields to expected names
        field_mapping = {
            "date_added": "date_added",
            "GPA": "GPA", 
            "GRE V": "GRE V",
            "GRE Q": "GRE Q", 
            "GRE AW": "GRE AW",
            "comments": "comments",
            "country_of_origin": "US/International"  # Map to expected field name
        }
        
        # Clean up the result
        cleaned_result = {}
        for key, value in result.items():
            if key in ["school", "notification_date"]:
                continue  # Skip these internal fields
            
            mapped_key = field_mapping.get(key, key)
            if value and str(value).strip():
                cleaned_result[mapped_key] = str(value).strip()
            else:
                cleaned_result[mapped_key] = None
        
        # Only return results that have meaningful data
        if cleaned_result.get("program"):
            return cleaned_result
        else:
            return None
    
    def _scrape_page_links(self, page_num: int = 1) -> List[str]:
        """Scrape detail page links from a single list page"""
        params = {'page': str(page_num)} if page_num > 1 else {}
        
        html = self._make_request(self.results_url, params)
        if not html:
            return []
        
        links = self._extract_detail_links(html)
        print(f"Found {len(links)} detail links on page {page_num}")
        return links
    
    def _scrape_detail_page(self, detail_url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single detail page"""
        html = self._make_request(detail_url)
        if not html:
            return None
        
        result = self._parse_detail_page(html, detail_url)
        return result
    
    def _get_max_pages(self) -> int:
        """Get the maximum number of pages from pagination"""
        try:
            html = self._make_request(self.results_url)
            if not html:
                return 1000  # Default fallback
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for pagination elements and extract the highest page number
            pagination_text = soup.get_text()
            page_numbers = re.findall(r'\b(\d{3,4})\b', pagination_text)
            
            if page_numbers:
                max_page = max(int(p) for p in page_numbers if int(p) < 10000)
                return max_page
            
            return 1000  # Default fallback
            
        except Exception as e:
            print(f"Could not determine max pages: {e}")
            return 1000
    
    def scrape_data(self, max_pages: int = None, target_entries: int = 30000) -> List[Dict[str, Any]]:
        """
        Main scraping method to collect grad cafe data
        
        Args:
            max_pages: Maximum number of list pages to scrape (None for auto-detect)
            target_entries: Target number of entries to collect
            
        Returns:
            List of scraped admission results
        """
        print("Starting Grad Cafe scraping...")
        print(f"Target: {target_entries} entries")
        
        if max_pages is None:
            max_pages = min(self._get_max_pages(), 1000)
            print(f"Detected max pages: {max_pages}")
        
        all_results = []
        page = 1
        consecutive_empty_pages = 0
        
        while page <= max_pages and len(all_results) < target_entries:
            print(f"Scraping list page {page}/{max_pages}...")
            
            # Get detail page links from this list page
            detail_links = self._scrape_page_links(page)
            
            if not detail_links:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 5:
                    print("Too many consecutive empty pages, stopping.")
                    break
                page += 1
                continue
            else:
                consecutive_empty_pages = 0
            
            # Scrape each detail page
            page_results = []
            for i, detail_url in enumerate(detail_links):
                if len(all_results) >= target_entries:
                    break
                
                print(f"  Scraping detail page {i+1}/{len(detail_links)}: {detail_url}")
                result = self._scrape_detail_page(detail_url)
                
                if result:
                    page_results.append(result)
                    all_results.append(result)
                
                # Rate limiting between detail page requests
                time.sleep(1.0)
            
            print(f"Successfully scraped {len(page_results)} results from page {page}")
            print(f"Total entries collected: {len(all_results)}")
            
            # Rate limiting between list pages
            time.sleep(2.0)
            page += 1
            
            # Progress update every 10 pages
            if page % 10 == 0:
                print(f"Progress: {len(all_results)} entries from {page} pages")
                
            # Save intermediate results every 50 pages
            if page % 50 == 0:
                self.scraped_data = all_results
                self.save_data(f"applicant_data_partial_{page}.json")
        
        self.scraped_data = all_results
        print(f"Scraping completed. Total entries: {len(all_results)}")
        return all_results
    
    def save_data(self, filename: str = "applicant_data.json") -> None:
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def load_data(self, filename: str = "applicant_data.json") -> List[Dict[str, Any]]:
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
    """Main function to run the scraper"""
    # Initialize scraper with proper email for identification
    scraper = GradCafeScraper(email="student.research@jhu.edu")
    
    print("Robots.txt compliance verified.")
    print("Please take a screenshot of https://www.thegradcafe.com/robots.txt")
    print("and save as robots_screenshot.jpg for assignment submission.")
    
    # Start with a small test to verify the approach works
    print("Starting with a small test (1 page, ~10-20 results)...")
    test_results = scraper.scrape_data(target_entries=20, max_pages=1)
    
    if test_results:
        print(f"\nTest successful! Found {len(test_results)} results.")
        print("Sample results:")
        for i, result in enumerate(test_results[:3]):
            print(f"\nResult {i+1}:")
            for key, value in result.items():
                if value:
                    print(f"  {key}: {value}")
        
        print(f"\nTest completed successfully. Ready to scrape full dataset.")
        print("Modify the max_pages parameter to scrape more data.")
        print("For 30,000 entries, you'll need approximately 1,500-3,000 pages.")
    else:
        print("Test failed - no results found. Please check the parsing logic.")
    
    # Save test results
    scraper.save_data("applicant_data_test.json")


if __name__ == "__main__":
    main()
