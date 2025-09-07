#!/usr/bin/env python3
"""
Data cleaning module for Grad Cafe scraped data
Cleans and standardizes the scraped admission results
"""

import json
import re
from typing import List, Dict, Any, Optional


class GradCafeDataCleaner:
    """Data cleaner for Grad Cafe admission results"""
    
    def __init__(self):
        self.cleaned_data = []
        
    def _clean_text(self, text: str) -> str:
        """Remove HTML tags and clean text"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        return text
    
    def _standardize_degree(self, degree: str) -> Optional[str]:
        """Standardize degree field"""
        if not degree:
            return None

        original = degree  # keep the exact input 
        degree = self._clean_text(degree).lower()
        
        # Map common degree variations
        if any(term in degree for term in ['phd', 'ph.d', 'doctorate', 'doctoral']):
            return "PhD"
        elif any(term in degree for term in ['masters', 'master', 'ms', 'm.s', 'ma', 'm.a', 'msc', 'm.sc']):
            return "Masters"
        elif any(term in degree for term in ['bachelor', 'bs', 'b.s', 'ba', 'b.a']):
            return "Bachelors"
        else:
            return original if original else None
    
    def _standardize_status(self, status: str) -> Optional[str]:
        """Standardize status field and extract dates"""
        if not status:
            return None
            
        status = self._clean_text(status)
        
        # Standardize common status variations
        status_lower = status.lower()
        if 'accept' in status_lower:
            return status  # Keep original for date extraction
        elif 'reject' in status_lower or 'denied' in status_lower:
            return status  # Keep original for date extraction
        elif 'wait' in status_lower:
            return "Wait listed"
        elif 'interview' in status_lower:
            return "Interview"
        else:
            return status
    
    def _standardize_term(self, term: str) -> Optional[str]:
        """Standardize term/season field"""
        if not term:
            return None
            
        term = self._clean_text(term)
        
        # Extract season and year
        season_match = re.search(r'(fall|spring|summer|winter)', term, re.IGNORECASE)
        year_match = re.search(r'(20\d{2})', term)
        
        if season_match and year_match:
            season = season_match.group(1).title()
            year = year_match.group(1)
            return f"{season} {year}"
        else:
            return term
    
    def _standardize_international_status(self, status: str) -> Optional[str]:
        """Standardize US/International field"""
        if not status:
            return None
            
        status = self._clean_text(status).lower()
        
        if 'international' in status or 'intl' in status:
            return "International"
        elif 'american' in status or 'us' in status or 'domestic' in status:
            return "American"
        else:
            return status.title() if status else None
    
    # def _extract_gpa(self, gpa_text: str) -> Optional[str]:
    #     """Extract and standardize GPA (old format with 'GPA ' prefix)"""
    #     if not gpa_text or gpa_text == "-":
    #         return None
            
    #     gpa_text = self._clean_text(gpa_text)
        
    #     # Extract GPA value
    #     gpa_match = re.search(r'(\d+\.?\d*)', gpa_text)
    #     if gpa_match:
    #         return f"GPA {gpa_match.group(1)}"
    #     else:
    #         return gpa_text if gpa_text else None
    
    def _extract_gpa_new_format(self, gpa_value: str) -> Optional[str]:
        """Extract and standardize GPA (new format - just the number)"""
        if not gpa_value or gpa_value == "-":
            return None
            
        gpa_value = self._clean_text(str(gpa_value))
        
        # For new format, the GPA is already just the number
        gpa_match = re.search(r'(\d+\.?\d*)', gpa_value)
        if gpa_match:
            return gpa_match.group(1)
        else:
            return gpa_value if gpa_value else None
    
    def _extract_gre_score(self, score_text: str, score_type: str) -> Optional[str]:
        """Extract and standardize GRE scores"""
        if not score_text or score_text == "-":
            return None
            
        score_text = self._clean_text(score_text)
        
        # Extract numeric score
        score_match = score_match = re.search(r'(\d+(?:\.\d+)?)', score_text) #re.search(r'(\d+)', score_text)
        if score_match:
            return score_match.group(1)
        else:
            return score_text if score_text else None
    
    def _clean_program_field(self, program: str) -> str:
        """Clean the program field for LLM processing"""
        if not program:
            return ""
            
        # Remove HTML and extra whitespace
        program = self._clean_text(program)
        
        # Remove common prefixes/suffixes that don't add value
        program = re.sub(r'^(program in|degree in|major in)\s+', '', program, flags=re.IGNORECASE)
        
        return program.strip()
    
    def _clean_single_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Clean a single data entry (new list view format only)"""
        cleaned_entry = {}
        
        # New format from list view scraper
        cleaned_entry["school"] = self._clean_text(entry.get("school", "")) or None
        cleaned_entry["major"] = self._clean_program_field(entry.get("major", ""))
        cleaned_entry["program"] = self._clean_program_field(entry.get("program", ""))
        cleaned_entry["degree"] = self._standardize_degree(entry.get("degree"))
        cleaned_entry["semester"] = self._standardize_term(entry.get("semester"))
        cleaned_entry["status"] = self._standardize_status(entry.get("status"))
        cleaned_entry["status_date"] = self._clean_text(entry.get("status_date", "")) or None
        cleaned_entry["date_added"] = self._clean_text(entry.get("date_added", "")) or None
        cleaned_entry["url"] = entry.get("url") or None
        cleaned_entry["applicant_type"] = self._standardize_international_status(entry.get("applicant_type"))
        cleaned_entry["gpa"] = self._extract_gpa_new_format(entry.get("gpa"))
        cleaned_entry["gre_total"] = self._extract_gre_score(entry.get("gre_total", ""), "Total")
        cleaned_entry["gre_verbal"] = self._extract_gre_score(entry.get("gre_verbal", ""), "Verbal")
        cleaned_entry["gre_quant"] = self._extract_gre_score(entry.get("gre_quant", ""), "Quantitative")
        cleaned_entry["gre_aw"] = self._extract_gre_score(entry.get("gre_aw", ""), "Analytical Writing")
        cleaned_entry["comments"] = self._clean_text(entry.get("comments", "")) or None
        
        return cleaned_entry
    
    def clean_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Main cleaning method to process all scraped data
        
        Args:
            raw_data: List of raw scraped entries
            
        Returns:
            List of cleaned entries
        """
        print(f"Starting data cleaning for {len(raw_data)} entries...")
        
        cleaned_entries = []
        
        for i, entry in enumerate(raw_data):
            try:
                cleaned_entry = self._clean_single_entry(entry)
                
                # Only keep entries with meaningful data
                if cleaned_entry.get("program") and cleaned_entry.get("program").strip():
                    cleaned_entries.append(cleaned_entry)
                    
            except Exception as e:
                print(f"Error cleaning entry {i}: {e}")
                continue
        
        self.cleaned_data = cleaned_entries
        print(f"Data cleaning completed. {len(cleaned_entries)} valid entries.")
        return cleaned_entries
    
    def remove_duplicates(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entries based on key fields"""
        seen = set()
        unique_data = []
        
        for entry in data:
            # Create a key based on program, status, and date
            key = (
                entry.get("program", "").lower(),
                entry.get("status", "").lower(),
                entry.get("date_added", "").lower(),
                entry.get("url", "")
            )
            
            if key not in seen:
                seen.add(key)
                unique_data.append(entry)
        
        print(f"Removed {len(data) - len(unique_data)} duplicate entries.")
        return unique_data
    
    def save_data(self, data: List[Dict[str, Any]], filename: str = "cleaned_applicant_data.json") -> None:
        """Save cleaned data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Cleaned data saved to {filename}")
        except Exception as e:
            print(f"Error saving cleaned data: {e}")
    
    def load_data(self, filename: str = "applicant_data.json") -> List[Dict[str, Any]]:
        """Load raw data from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Data loaded from {filename}: {len(data)} entries")
            return data
        except Exception as e:
            print(f"Error loading data: {e}")
            return []
    
    def get_data_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics about the cleaned data (new format only)"""
        if not data:
            return {}
        
        stats = {
            "total_entries": len(data),
            "entries_with_program": sum(1 for entry in data if entry.get("program")),
            "entries_with_degree": sum(1 for entry in data if entry.get("degree")),
            "entries_with_school": sum(1 for entry in data if entry.get("school")),
            "entries_with_major": sum(1 for entry in data if entry.get("major")),
            "entries_with_gpa": sum(1 for entry in data if entry.get("gpa")),
            "entries_with_gre_total": sum(1 for entry in data if entry.get("gre_total")),
            "entries_with_gre_verbal": sum(1 for entry in data if entry.get("gre_verbal")),
            "entries_with_gre_quant": sum(1 for entry in data if entry.get("gre_quant")),
            "entries_with_gre_aw": sum(1 for entry in data if entry.get("gre_aw")),
            "entries_with_comments": sum(1 for entry in data if entry.get("comments")),
            "entries_with_semester": sum(1 for entry in data if entry.get("semester")),
            "unique_programs": len(set(entry.get("program", "").lower() for entry in data if entry.get("program"))),
            "unique_schools": len(set(entry.get("school", "").lower() for entry in data if entry.get("school"))),
        }
        
        return stats


def main():
    """Main function to run the data cleaner"""
    cleaner = GradCafeDataCleaner()
    
    # Load raw data from list view scraper (new format)
    raw_data = cleaner.load_data("applicant_data.json")
    
    if not raw_data:
        print("No data found to clean. Please run scrape_list_view.py first.")
        return
    
    # Clean the data
    cleaned_data = cleaner.clean_data(raw_data)
    
    # Remove duplicates
    unique_data = cleaner.remove_duplicates(cleaned_data)
    
    # Save cleaned data
    cleaner.save_data(unique_data, "cleaned_applicant_data.json")
    
    # Print statistics
    stats = cleaner.get_data_statistics(unique_data)
    print("\nData Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\nData cleaning complete! {len(unique_data)} entries ready for LLM processing.")


if __name__ == "__main__":
    main()
