#!/usr/bin/env python3
"""
Incremental scraper for Grad Cafe data
Modified version that only scrapes NEW data based on database timestamps
"""

import json
import re
import time
import urllib3
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
import urllib.robotparser
import psycopg
from datetime import datetime, date
import sys
import os

# Add the current directory to Python path to import existing modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scrape import GradCafeListScraper

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'gradcafe_db',
    'user': 'momo',
    'password': ''
}

class IncrementalGradCafeScraper(GradCafeListScraper):
    """Extended scraper that only collects new data based on database timestamps"""
    
    def __init__(self, email: str = "wliu125@jh.edu", db_config: Dict = None):
        super().__init__(email)
        self.db_config = db_config or DB_CONFIG
        self.latest_db_date = None
        
    def get_latest_database_date(self) -> Optional[date]:
        """Get the most recent date_added from the database"""
        try:
            connection = psycopg.connect(**self.db_config)
            with connection.cursor() as cursor:
                cursor.execute("SELECT MAX(date_added) FROM applicant_data")
                result = cursor.fetchone()
                latest_date = result[0] if result and result[0] else None
                
            connection.close()
            
            if latest_date:
                print(f"Latest date in database: {latest_date}")
                return latest_date
            else:
                print("No existing data found in database")
                return None
                
        except Exception as e:
            print(f"Error querying database: {e}")
            return None
    
    def is_entry_newer(self, entry_date_str: str, cutoff_date: date) -> bool:
        """Check if an entry's date is newer than the cutoff date"""
        if not entry_date_str or not cutoff_date:
            return True  # Include if we can't determine
        
        try:
            # Parse various date formats from GradCafe
            # Examples: "September 06, 2025", "Sep 6, 2025", "9/6/2025"
            
            # Try different date parsing approaches
            for fmt in ["%B %d, %Y", "%b %d, %Y", "%m/%d/%Y", "%Y-%m-%d"]:
                try:
                    entry_date = datetime.strptime(entry_date_str.strip(), fmt).date()
                    return entry_date > cutoff_date
                except ValueError:
                    continue
            
            # If no format matches, include the entry to be safe
            print(f"Could not parse date: {entry_date_str}")
            return True
            
        except Exception as e:
            print(f"Error parsing date {entry_date_str}: {e}")
            return True
    
    def scrape_new_data_only(self, max_pages: int = 100) -> List[Dict[str, Any]]:
        """
        Scrape only new data that's not already in the database
        
        Args:
            max_pages: Maximum number of pages to check for new data
            
        Returns:
            List of new admission results
        """
        print("Starting incremental Grad Cafe scraping...")
        
        # Get the latest date from database
        self.latest_db_date = self.get_latest_database_date()
        
        if not self.latest_db_date:
            print("No existing data found. Consider running full scraper first.")
            return []
        
        print(f"Looking for entries newer than: {self.latest_db_date}")
        
        new_results = []
        page = 1
        consecutive_old_pages = 0
        
        while page <= max_pages:
            print(f"Checking page {page} for new data...")
            
            # Make request with page parameter
            params = {'page': str(page)} if page > 1 else {}
            html = self._make_request(self.results_url, params)
            
            if not html:
                print(f"Failed to fetch page {page}")
                page += 1
                continue
            
            # Parse the page
            page_results = self._parse_list_page(html)
            
            if not page_results:
                print(f"No results found on page {page}")
                page += 1
                continue
            
            # Filter for new entries only
            new_entries_on_page = []
            old_entries_count = 0
            
            for entry in page_results:
                entry_date_str = entry.get('date_added')
                if entry_date_str and self.is_entry_newer(entry_date_str, self.latest_db_date):
                    new_entries_on_page.append(entry)
                else:
                    old_entries_count += 1
            
            if new_entries_on_page:
                new_results.extend(new_entries_on_page)
                print(f"  Found {len(new_entries_on_page)} new entries on page {page}")
                consecutive_old_pages = 0
            else:
                consecutive_old_pages += 1
                print(f"  No new entries on page {page} ({old_entries_count} old entries)")
            
            # If we've seen several pages with no new data, we're probably done
            if consecutive_old_pages >= 5:
                print("Found several consecutive pages with no new data. Stopping.")
                break
            
            # Rate limiting
            time.sleep(0.5)
            page += 1
            
            # Progress update
            if len(new_results) > 0 and len(new_results) % 50 == 0:
                print(f"Progress: {len(new_results)} new entries found")
        
        print(f"Incremental scraping completed. New entries found: {len(new_results)}")
        return new_results
    
    def save_new_data(self, new_data: List[Dict[str, Any]], filename: str = "new_applicant_data.json") -> None:
        """Save only the new scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
            print(f"New data saved to {filename}")
        except Exception as e:
            print(f"Error saving new data: {e}")

def main():
    """Main function to run incremental scraping"""
    print("=" * 60)
    print("Incremental Grad Cafe Scraper")
    print("=" * 60)
    
    # Initialize incremental scraper
    scraper = IncrementalGradCafeScraper(email="wliu125@jh.edu")
    
    # Scrape only new data
    new_results = scraper.scrape_new_data_only(max_pages=50)
    
    if new_results:
        # Save new data
        scraper.save_new_data(new_results, "new_applicant_data.json")
        print(f"\nFound {len(new_results)} new entries!")
        
        # Show sample of new data
        print("\nSample of new entries:")
        for i, entry in enumerate(new_results[:3]):
            print(f"{i+1}. {entry.get('program', 'N/A')} - {entry.get('status', 'N/A')} - {entry.get('date_added', 'N/A')}")
    else:
        print("No new data found.")
    
    return len(new_results)

if __name__ == "__main__":
    new_count = main()
    sys.exit(0 if new_count >= 0 else 1)
