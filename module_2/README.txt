Name: Wei Liu, wliu125@jh.edu
Module Info: Module 2 - Web Scraping and Data Cleaning Assignment
Due Date: 9/7/2025

APPROACH:

This assignment implements a complete pipeline for scraping, cleaning, and standardizing graduate school admission data from The Grad Cafe website. The solution consists of three main components:

1. WEB SCRAPING (scrape.py):
   - Implemented using a GradCafeScraper class that utilizes urllib3 for HTTP requests
   - Uses BeautifulSoup for HTML parsing to extract admission results from table structures
   - Implements rate limiting (0.5 second delays) to be respectful to the server
   - Extracts the following data fields:
     * Program Name and University (combined in program field)
     * Degree type (Masters/PhD)
     * Application term/season
     * Admission status (Accepted/Rejected/Wait listed)
     * Date information was added to Grad Cafe
     * URL link to the specific result entry
     * Student type (US/International)
     * GPA information
     * GRE scores (Verbal, Quantitative, Analytical Writing)
     * Comments from applicants
   - Targets 50,000 entries by iterating through multiple pages
   - Saves raw data to applicant_data.json

2. DATA CLEANING (clean.py):
   - Implemented using a GradCafeDataCleaner class
   - Removes HTML tags and entities from scraped text
   - Standardizes degree types (PhD, Masters, Bachelors)
   - Normalizes status fields and extracts date information
   - Standardizes term/season formatting (e.g., "Fall 2024")
   - Cleans and extracts numeric GPA and GRE scores
   - Removes duplicate entries based on key field combinations
   - Handles missing data consistently (None for unavailable fields)
   - Saves cleaned data to cleaned_applicant_data.json

3. LLM STANDARDIZATION (llm_hosting/):
   - Uses the provided TinyLlama model to standardize program and university names
   - Addresses the problem of inconsistent naming (e.g., "JHU" vs "Johns Hopkins University")
   - Implements few-shot prompting with examples for better accuracy
   - Includes fallback rules for common abbreviations and misspellings
   - Uses fuzzy matching against canonical lists for post-processing
   - Adds two new fields: llm-generated-program and llm-generated-university

DATA STRUCTURES:
- Raw scraped data: List of dictionaries with string keys for each data field
- Cleaned data: Same structure but with standardized values and None for missing data
- LLM output: Enhanced data with additional standardized program/university fields

ALGORITHMS:
- Web scraping: Iterative page-by-page extraction with BeautifulSoup table parsing
- Data cleaning: Rule-based text processing with regex pattern matching
- Deduplication: Hash-based duplicate detection using key field combinations
- LLM standardization: Few-shot prompting with post-processing normalization

ROBOTS.TXT COMPLIANCE:
- Manually verified robots.txt at https://www.thegradcafe.com/robots.txt
- Screenshot saved as robots_txt_screenshot.jpg
- Confirmed that academic research scraping is permitted
- Implemented respectful rate limiting to avoid server overload

USAGE INSTRUCTIONS:
1. Install dependencies: pip install -r requirements.txt
2. Run scraper: python scrape.py
3. Clean data: python clean.py
4. Standardize with LLM: cd llm_hosting && python app.py --file ../cleaned_applicant_data.json --stdout > ../llm_extend_applicant_data.json

DELIVERABLES:
- scrape.py: Web scraping implementation
- clean.py: Data cleaning implementation
- requirements.txt: Python dependencies
- applicant_data.json: Raw scraped data (50,000 entries)
- cleaned_applicant_data.json: Cleaned data ready for LLM processing
- llm_extend_applicant_data.json: Final standardized data with LLM enhancements
- robots_screenshot.jpg: Evidence of robots.txt compliance check
- llm_hosting/: Complete LLM standardization package

The solution follows all SHALL requirements:
- Uses only urllib3, BeautifulSoup, and other specified libraries
- Extracts all required data categories
- Includes 30,000+ entries
- Complies with robots.txt
- Uses Python 3.10+
- Implements proper function/class structure
- Saves data in structured JSON format

KNOWN BUGS:
No known bugs in the current implementation. The code includes comprehensive error handling and has been tested with sample data. If any issues arise during execution, they would likely be related to:
- Network connectivity issues during scraping
- Changes to The Grad Cafe website structure
- Memory limitations when processing large datasets

These could be addressed by:
- Adding retry logic for network requests
- Updating parsing logic if website structure changes
- Implementing batch processing for memory efficiency

EDGE CASES HANDLED:
- Missing or malformed data fields
- HTML entities and tags in scraped content
- Duplicate entries across pages
- Various date and score formats
- Network timeouts and HTTP errors
- Empty or null values in data fields
