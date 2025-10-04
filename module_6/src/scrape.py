#!/usr/bin/env python3
"""
List view scraper for Grad Cafe data.

Scrapes graduate school admission results from thegradcafe.com list view.
This approach is more efficient than scraping individual detail pages.
"""

import json
import re
import time
import urllib.robotparser
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import urllib3
from bs4 import BeautifulSoup


class GradCafeListScraper:
    """
    Web scraper for Grad Café admission results using the list view.

    Provides HTTP fetching with retries/backoff, robots.txt checking, HTML parsing
    to structured dictionaries, pagination handling, and JSON export.
    """

    def __init__(self, email: str = "wliu125@jh.edu"):
        """
        Initialize the list-view scraper.

        :param email: Contact email to include in the User-Agent for responsible scraping.
        :type email: str
        """
        self.http = urllib3.PoolManager()
        self.base_url = "https://www.thegradcafe.com"
        self.results_url = "https://www.thegradcafe.com/survey/index.php"
        self.scraped_data = []
        self.email = email
        self.user_agent = f"Academic Research Bot (+{email})"

        # Check robots.txt compliance
        self._check_robots_txt()

    def _check_robots_txt(self) -> bool:
        """
        Programmatically check robots.txt compliance.

        :return: True if fetching the results URL is permitted for this user agent, False otherwise.
        :rtype: bool
        """
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

        except urllib3.exceptions.HTTPError as exc:
            print(f"Could not check robots.txt: {exc}")
            print("Proceeding with caution...")
            return True

    def _make_request(
        self, url: str, params: Optional[Dict] = None, retry_count: int = 3
    ) -> Optional[str]:
        """
        Make an HTTP GET request with error handling, rate limiting, and retries.

        Uses exponential backoff for 429 and 5xx responses.

        :param url: Base URL to request.
        :type url: str
        :param params: Optional querystring parameters to append.
        :type params: dict | None
        :param retry_count: Maximum number of retry attempts.
        :type retry_count: int
        :return: Response body as UTF-8 string, or None on failure.
        :rtype: str | None
        """
        if params:
            query_string = urlencode(params)
            url = f"{url}?{query_string}"

        for attempt in range(retry_count):
            try:
                response = self.http.request(
                    "GET", url, headers={"User-Agent": self.user_agent}, timeout=30.0
                )

                if response.status == 200:
                    return response.data.decode("utf-8")
                if response.status == 429:  # Rate limited
                    wait_time = 2**attempt  # Exponential backoff
                    print(f"Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                if response.status >= 500:  # Server error
                    wait_time = 2**attempt
                    print(f"Server error {response.status}, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                print(f"HTTP {response.status} error for URL: {url}")
                return None

            except (urllib3.exceptions.HTTPError, TimeoutError) as exc:
                wait_time = 2**attempt
                print(f"Request failed (attempt {attempt + 1}): {exc}")
                if attempt < retry_count - 1:
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    return None

        return None

    def _extract_semester(self, row_element) -> Optional[str]:
        """
        Extract a semester string from a row (e.g., ``"Fall 2026"``).

        :param row_element: BeautifulSoup element for the table row.
        :type row_element: bs4.element.Tag
        :return: Semester string if found, else None.
        :rtype: str | None
        """
        # Look for semester badges (usually orange/colored badges)
        badges = row_element.find_all(["span", "div"], class_=re.compile(r"badge|label|tag", re.I))

        for badge in badges:
            text = badge.get_text(strip=True)
            # Match patterns like "Fall 2026", "Spring 2025", etc.
            if re.match(r"^(Fall|Spring|Summer|Winter)\s+\d{4}$", text, re.I):
                return text

        # Alternative: Look in text content
        text_content = row_element.get_text()
        semester_match = re.search(r"\b(Fall|Spring|Summer|Winter)\s+\d{4}\b", text_content, re.I)
        if semester_match:
            return semester_match.group(0)

        return None

    def _extract_status_info(self, row_element) -> Dict[str, Optional[str]]:
        """
        Extract acceptance status and date from a row.

        Recognizes patterns like: ``Accepted on 1 Sep``, ``Rejected on 2 Sep``,
        ``Interview on 15 Mar``, and ``Wait listed on 6 Feb`` (normalized to
        ``Waitlisted``).

        :param row_element: BeautifulSoup element for the table row.
        :type row_element: bs4.element.Tag
        :return: Dict with keys ``status`` and ``status_date``.
        :rtype: dict
        """
        status_info = {"status": None, "status_date": None}

        # Look for status text patterns
        text = row_element.get_text()

        # Pattern: "Accepted on 1 Sep", "Rejected on 2 Sep", etc.
        # Handle both "Waitlisted" and "Wait listed" (with space)
        status_pattern = (
            r"(Accepted|Rejected|Interview|Wait\s*listed|Waitlisted)"
            r"\s+on\s+(\d{1,2}\s+\w+)"
        )
        match = re.search(status_pattern, text, re.I)

        if match:
            # Normalize "Wait listed" to "Waitlisted" for consistency
            status = match.group(1)
            if "wait" in status.lower():
                status_info["status"] = "Waitlisted"
            else:
                status_info["status"] = status.capitalize()
            status_info["status_date"] = match.group(2)
        else:
            # Look for status in specific elements
            for elem in row_element.find_all(["span", "div", "td"]):
                elem_text = elem.get_text(strip=True)

                if re.match(
                    r"^(Accepted|Rejected|Interview|Wait\s*listed|Waitlisted)$",
                    elem_text,
                    re.I,
                ):
                    # Normalize "Wait listed" to "Waitlisted"
                    if "wait" in elem_text.lower():
                        status_info["status"] = "Waitlisted"
                    else:
                        status_info["status"] = elem_text.capitalize()
                    break

        return status_info

    def _extract_basic_info(self, cells) -> Dict[str, Any]:
        """Extract basic information from main row cells."""
        result = {}

        # Extract school (first column)
        result["school"] = cells[0].get_text(strip=True)

        # Extract major and degree (second column)
        program_div = cells[1].find("div", class_="tw-text-gray-900")
        if program_div:
            spans = program_div.find_all("span")
            if spans:
                result["major"] = spans[0].get_text(strip=True)
                result["degree"] = spans[-1].get_text(strip=True) if len(spans) > 1 else None
            else:
                result["major"] = None
        else:
            result["major"] = None

        # Create combined program field
        school = result.get("school", "").strip()
        major = result.get("major", "").strip()

        if major and school:
            result["program"] = f"{major}, {school}"
        elif major:
            result["program"] = major
        elif school:
            result["program"] = school
        else:
            result["program"] = None

        return result

    def _extract_status_from_cells(self, cells) -> Dict[str, Any]:
        """Extract status information from cells."""
        result = {}

        # Extract date added
        if len(cells) > 2:
            result["date_added"] = cells[2].get_text(strip=True)

        # Extract status
        if len(cells) > 3:
            status_div = cells[3].find(
                "div", class_=re.compile(r"tw-inline-flex.*tw-items-center")
            )
            if status_div:
                status_text = status_div.get_text(strip=True)
                status_match = re.match(
                    r"(Accepted|Rejected|Interview|Wait\s*listed|Waitlisted)\s+on\s+(.+)",
                    status_text,
                    re.I,
                )
                if status_match:
                    status = status_match.group(1)
                    if "wait" in status.lower():
                        result["status"] = "Waitlisted"
                    else:
                        result["status"] = status.capitalize()
                    result["status_date"] = status_match.group(2)
                else:
                    result["status"] = status_text
                    result["status_date"] = None

        return result

    def _extract_badge_info(self, badge_text) -> Dict[str, Any]:
        """Extract information from a badge."""
        result = {}

        # Extract semester
        if re.match(r"^(Fall|Spring|Summer|Winter)\s+\d{4}$", badge_text, re.I):
            result["semester"] = badge_text

        # Extract applicant type
        elif badge_text.lower() in ["international", "american", "domestic", "us"]:
            result["applicant_type"] = badge_text.capitalize()

        # Extract GPA
        elif badge_text.startswith("GPA"):
            gpa_match = re.search(r"GPA\s*(\d+\.\d+)", badge_text)
            if gpa_match:
                result["gpa"] = gpa_match.group(1)

        # Extract GRE scores
        elif "GRE" in badge_text:
            self._extract_gre_from_badge(badge_text, result)

        return result

    def _extract_gre_from_badge(self, badge_text, result):
        """Extract GRE scores from badge text."""
        if badge_text.startswith("GRE V"):
            match = re.search(r"GRE V\s*(\d+)", badge_text)
            if match:
                result["gre_verbal"] = match.group(1)
        elif badge_text.startswith("GRE Q"):
            match = re.search(r"GRE Q\s*(\d+)", badge_text)
            if match:
                result["gre_quant"] = match.group(1)
        elif badge_text.startswith("GRE AW"):
            match = re.search(r"GRE AW\s*(\d+(?:\.\d+)?)", badge_text)
            if match:
                result["gre_aw"] = match.group(1)
        elif badge_text.startswith("GRE"):
            match = re.search(r"GRE\s*(\d+)", badge_text)
            if match:
                result["gre_total"] = match.group(1)

    def _parse_list_entry(
        self, main_row, detail_row=None, comment_row=None
    ) -> Optional[Dict[str, Any]]:
        """
        Parse one logical entry from the list.

        :param main_row: Main table row containing school, program, date, status columns.
        :type main_row: bs4.element.Tag
        :param detail_row: Optional detail row with badges (semester, GRE, GPA, etc.).
        :type detail_row: bs4.element.Tag | None
        :param comment_row: Optional comment row.
        :type comment_row: bs4.element.Tag | None
        :return: Parsed entry as a dictionary or None if the row structure is invalid.
        :rtype: dict | None
        """
        try:
            cells = main_row.find_all("td")
            if len(cells) < 4:
                return None

            # Extract basic info
            result = self._extract_basic_info(cells)

            # Extract status info
            result.update(self._extract_status_from_cells(cells))

            # Extract URL
            link = main_row.find("a", href=re.compile(r"/result/\d+"))
            if link:
                result["url"] = self.base_url + link.get("href")

            # Parse detail row
            if detail_row:
                badges = detail_row.find_all(
                    "div",
                    class_=re.compile(r"tw-inline-flex.*tw-items-center.*tw-rounded-md"),
                )
                for badge in badges:
                    badge_text = badge.get_text(strip=True)
                    result.update(self._extract_badge_info(badge_text))

            # Parse comment row
            if comment_row:
                comment_p = comment_row.find("p", class_="tw-text-gray-500")
                if comment_p:
                    result["comments"] = comment_p.get_text(strip=True)

            # Set defaults for missing fields
            default_fields = [
                "semester", "applicant_type", "gpa", "gre_total",
                "gre_verbal", "gre_quant", "gre_aw", "comments"
            ]
            for field in default_fields:
                if field not in result:
                    result[field] = None

            return result

        except (AttributeError, KeyError, TypeError) as exc:
            print(f"Error parsing entry: {exc}")
            return None

    def _find_table(self, soup):
        """Find the results table in the page."""
        table = soup.find("table", class_="tw-min-w-full")
        if not table:
            tables = soup.find_all("table")
            table = tables[0] if tables else None
        return table

    def _get_detail_row(self, rows, index):
        """Get detail row if it exists."""
        if index + 1 >= len(rows):
            return None, index

        next_row = rows[index + 1]
        if "tw-border-none" in next_row.get("class", []):
            return next_row, index + 1
        return None, index

    def _get_comment_row(self, rows, index):
        """Get comment row if it exists."""
        if index + 1 >= len(rows):
            return None, index

        potential_comment = rows[index + 1]
        if "tw-border-none" not in potential_comment.get("class", []):
            return None, index

        if potential_comment.find("p", class_="tw-text-gray-500"):
            return potential_comment, index + 1
        return None, index

    def _parse_list_page(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse a full list page, returning all admission results found.

        :param html: HTML content of the list page.
        :type html: str
        :return: List of parsed entry dictionaries.
        :rtype: list[dict]
        """
        soup = BeautifulSoup(html, "html.parser")
        results = []

        table = self._find_table(soup)
        if not table:
            print("No table found on page")
            return results

        tbody = table.find("tbody") or table
        rows = tbody.find_all("tr")

        i = 0
        while i < len(rows):
            row = rows[i]

            # Skip header rows
            if row.find("th") and not row.find("td"):
                i += 1
                continue

            cells = row.find_all("td")
            if len(cells) < 4:
                i += 1
                continue

            # Process main row and associated rows
            main_row = row
            detail_row, i = self._get_detail_row(rows, i)
            comment_row, i = self._get_comment_row(rows, i)

            # Parse the complete entry
            result = self._parse_list_entry(main_row, detail_row, comment_row)
            if result and result.get("school"):
                results.append(result)

            i += 1

        return results

    def _get_total_pages(self) -> int:
        """
        Determine the total number of available pages.

        Attempts to parse pagination UI or "Page X of Y" text; falls back to a high
        sentinel value if undeterminable.

        :return: Total number of pages, or a conservative upper bound if unknown.
        :rtype: int
        """
        try:
            html = self._make_request(self.results_url)
            if not html:
                return 1

            soup = BeautifulSoup(html, "html.parser")

            # Look for pagination elements
            pagination = soup.find(["div", "nav", "ul"], class_=re.compile(r"paginat", re.I))
            if pagination:
                # Find all page numbers
                page_links = pagination.find_all("a", string=re.compile(r"^\d+$"))
                if page_links:
                    page_numbers = [int(link.get_text()) for link in page_links]
                    return max(page_numbers)

            # Alternative: Look for "Page X of Y" text
            page_text = soup.get_text()
            match = re.search(r"Page\s+\d+\s+of\s+(\d+)", page_text, re.I)
            if match:
                return int(match.group(1))

            # Default fallback
            return 1000

        except (AttributeError, ValueError, TypeError) as exc:
            print(f"Could not determine total pages: {exc}")
            return 1000

    def scrape_data(
        self, max_pages: int = None, target_entries: int = 30000
    ) -> List[Dict[str, Any]]:
        """
        Scrape list-view pages until reaching ``max_pages`` or ``target_entries``.

        Respects a small delay between page requests. Stores full results in
        :pyattr:`scraped_data` and returns them.

        :param max_pages: Maximum pages to scrape (``None`` auto-detects and caps to 1500).
        :type max_pages: int | None
        :param target_entries: Target number of entries to collect before stopping.
        :type target_entries: int
        :return: All parsed results collected.
        :rtype: list[dict]
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
            params = {"page": str(page)} if page > 1 else {}
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
            time.sleep(0.5)  # Be respectful to the server

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
        """
        Save scraped data to a JSON file.

        :param filename: Output filename for the JSON array.
        :type filename: str
        :return: None
        :rtype: None
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {filename}")
        except IOError as exc:
            print(f"Error saving data: {exc}")


def main():
    """
    Command-line entry point for the list-view scraper.

    Scrapes up to the configured limits and writes the final JSON file.

    :return: None
    :rtype: None
    """
    # Initialize scraper with proper email for identification
    scraper = GradCafeListScraper(email="wei.liu125@jh.edu")

    print("=" * 60)
    print("Grad Cafe List View Scraper")
    print("=" * 60)

    # Start with a small test to verify the approach works
    # print("\nStarting with a small test (2 pages)...")
    # test_results = scraper.scrape_data(max_pages=2, target_entries=50)

    # if test_results:
    #     print(f"\nTest successful! Found {len(test_results)} results.")
    #     print("\nSample results:")

    #     # Show semester data specifically
    #     semesters = [r.get('semester') for r in test_results if r.get('semester')]
    #     if semesters:
    #         print(f"\nSemester data found: {set(semesters)}")

    #     print(f"\nTest completed successfully.")
    #     print("To scrape more data, increase max_pages parameter.")
    #     print("For 30,000 entries, you'll need approximately 1,500 pages.")
    # else:
    #     print("Test failed - no results found. Please check the website structure.")

    # Save test results
    # scraper.save_data("applicant_data_list_test.json")

    # For production
    scraper.scrape_data(max_pages=3000, target_entries=50000)
    scraper.save_data("applicant_data.json")


if __name__ == "__main__":
    main()
