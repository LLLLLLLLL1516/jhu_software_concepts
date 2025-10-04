#!/usr/bin/env python3
"""
Data cleaning module for Grad Cafe scraped data.

This module provides the :class:`GradCafeDataCleaner` class for cleaning
and standardizing scraped admission results. It handles normalization
of text fields, GPA/GRE extraction, duplicate removal, and output to JSON.
"""

import json
import re
from typing import Any, Dict, List, Optional


class GradCafeDataCleaner:
    """
    Data cleaner for Grad Cafe admission results.

    Provides methods to clean, normalize, and deduplicate scraped data
    from Grad Cafe for downstream analysis or storage.
    """

    def __init__(self):
        """Initialize the cleaner with an empty dataset."""
        self.cleaned_data = []

    def _clean_text(self, text: str) -> str:
        """
        Remove HTML tags, extra whitespace, and common entities.

        :param text: Input text possibly containing HTML tags or entities.
        :type text: str
        :return: Cleaned text with tags removed and entities replaced.
        :rtype: str
        """
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove common HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')

        return text

    def _standardize_degree(self, degree: str) -> Optional[str]:
        """
        Standardize the degree field into categories (PhD, Masters, Bachelors).

        :param degree: Raw degree string.
        :type degree: str
        :return: Standardized degree string or None if empty.
        :rtype: Optional[str]
        """
        if not degree:
            return None

        original = degree  # keep the exact input
        degree = self._clean_text(degree).lower()

        # Map common degree variations
        if any(term in degree for term in ["phd", "ph.d", "doctorate", "doctoral"]):
            return "PhD"
        if any(
            term in degree
            for term in ["masters", "master", "ms", "m.s", "ma", "m.a", "msc", "m.sc"]
        ):
            return "Masters"
        if any(term in degree for term in ["bachelor", "bs", "b.s", "ba", "b.a"]):
            return "Bachelors"
        return original if original else None

    def _standardize_status(self, status: str) -> Optional[str]:
        """
        Standardize admission status values.

        :param status: Raw status string.
        :type status: str
        :return: Standardized status string or None if empty.
        :rtype: Optional[str]
        """
        if not status:
            return None

        status = self._clean_text(status)

        # Standardize common status variations
        status_lower = status.lower()
        if "accept" in status_lower:
            return status  # Keep original for date extraction
        if "reject" in status_lower or "denied" in status_lower:
            return status  # Keep original for date extraction
        if "wait" in status_lower:
            return "Wait listed"
        if "interview" in status_lower:
            return "Interview"
        return status

    def _standardize_term(self, term: str) -> Optional[str]:
        """
        Standardize the term/season field.

        :param term: Raw term string (e.g., "Fall 2024").
        :type term: str
        :return: Standardized term string or None if not parseable.
        :rtype: Optional[str]
        """
        if not term:
            return None

        term = self._clean_text(term)

        # Extract season and year
        season_match = re.search(r"(fall|spring|summer|winter)", term, re.IGNORECASE)
        year_match = re.search(r"(20\d{2})", term)

        if season_match and year_match:
            season = season_match.group(1).title()
            year = year_match.group(1)
            return f"{season} {year}"
        return term

    def _standardize_international_status(self, status: str) -> Optional[str]:
        """
        Standardize the US/International applicant field.

        :param status: Raw applicant type string.
        :type status: str
        :return: Standardized "International" or "American", or cleaned value.
        :rtype: Optional[str]
        """
        if not status:
            return None

        status = self._clean_text(status).lower()

        if "international" in status or "intl" in status:
            return "International"
        if "american" in status or "us" in status or "domestic" in status:
            return "American"
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
        """
        Extract and standardize GPA values (numeric only).

        :param gpa_value: Raw GPA string or number.
        :type gpa_value: str
        :return: Extracted GPA number as string, or None if invalid.
        :rtype: Optional[str]
        """
        if not gpa_value or gpa_value == "-":
            return None

        gpa_value = self._clean_text(str(gpa_value))

        # For new format, the GPA is already just the number
        gpa_match = re.search(r"(\d+\.?\d*)", gpa_value)
        if gpa_match:
            return gpa_match.group(1)
        return gpa_value if gpa_value else None

    def _extract_gre_score(self, score_text: str, score_type: str) -> Optional[str]:
        """
        Extract and standardize GRE scores.

        :param score_text: Raw GRE score string.
        :type score_text: str
        :param score_type: GRE section type (Total, Verbal, Quantitative, Analytical Writing).
        :type score_type: str
        :return: Extracted GRE score as string, or None if invalid.
        :rtype: Optional[str]
        """
        # score_type is kept for potential future use or logging
        _ = score_type

        if not score_text or score_text == "-":
            return None

        score_text = self._clean_text(score_text)

        # Extract numeric score
        score_match = re.search(r"(\d+(?:\.\d+)?)", score_text)
        if score_match:
            return score_match.group(1)
        return score_text if score_text else None

    def _clean_program_field(self, program: str) -> str:
        """
        Clean the program field for standardization.

        :param program: Raw program string.
        :type program: str
        :return: Cleaned program string.
        :rtype: str
        """
        if not program:
            return ""

        # Remove HTML and extra whitespace
        program = self._clean_text(program)

        # Remove common prefixes/suffixes that don't add value
        program = re.sub(r"^(program in|degree in|major in)\s+", "", program, flags=re.IGNORECASE)

        return program.strip()

    def _clean_single_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean a single scraped entry.

        :param entry: Raw scraped entry dictionary.
        :type entry: dict
        :return: Cleaned entry dictionary.
        :rtype: dict
        """
        # Handle None entries
        if entry is None:
            raise TypeError("Entry cannot be None")

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
        cleaned_entry["applicant_type"] = self._standardize_international_status(
            entry.get("applicant_type")
        )
        cleaned_entry["gpa"] = self._extract_gpa_new_format(entry.get("gpa"))
        cleaned_entry["gre_total"] = self._extract_gre_score(entry.get("gre_total", ""), "Total")
        cleaned_entry["gre_verbal"] = self._extract_gre_score(entry.get("gre_verbal", ""), "Verbal")
        cleaned_entry["gre_quant"] = self._extract_gre_score(
            entry.get("gre_quant", ""), "Quantitative"
        )
        cleaned_entry["gre_aw"] = self._extract_gre_score(
            entry.get("gre_aw", ""), "Analytical Writing"
        )
        cleaned_entry["comments"] = self._clean_text(entry.get("comments", "")) or None

        return cleaned_entry

    def clean_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean a list of raw scraped entries.

        :param raw_data: List of raw entries from the scraper.
        :type raw_data: list[dict]
        :return: List of cleaned entries.
        :rtype: list[dict]
        """
        print(f"Starting data cleaning for {len(raw_data)} entries...")

        cleaned_entries = []

        for i, entry in enumerate(raw_data):
            try:
                cleaned_entry = self._clean_single_entry(entry)

                # Only keep entries with meaningful data
                if cleaned_entry.get("program") and cleaned_entry.get("program").strip():
                    cleaned_entries.append(cleaned_entry)

            except (KeyError, TypeError, ValueError) as exc:
                print(f"Error cleaning entry {i}: {exc}")
                continue

        self.cleaned_data = cleaned_entries
        print(f"Data cleaning completed. {len(cleaned_entries)} valid entries.")
        return cleaned_entries

    def remove_duplicates(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate entries based on program, status, date, and URL.

        :param data: List of cleaned entries.
        :type data: list[dict]
        :return: List with duplicates removed.
        :rtype: list[dict]
        """
        seen = set()
        unique_data = []

        for entry in data:
            # Create a key based on program, status, and date
            key = (
                (entry.get("program") or "").lower(),
                (entry.get("status") or "").lower(),
                (entry.get("date_added") or "").lower(),
                entry.get("url", ""),
            )

            if key not in seen:
                seen.add(key)
                unique_data.append(entry)

        print(f"Removed {len(data) - len(unique_data)} duplicate entries.")
        return unique_data

    def save_data(
        self, data: List[Dict[str, Any]], filename: str = "cleaned_applicant_data.json"
    ) -> None:
        """
        Save cleaned data to a JSON file.

        :param data: Cleaned data to save.
        :type data: list[dict]
        :param filename: Output JSON file path.
        :type filename: str
        """
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Cleaned data saved to {filename}")
        except IOError as exc:
            print(f"Error saving cleaned data: {exc}")

    def load_data(self, filename: str = "applicant_data.json") -> List[Dict[str, Any]]:
        """
        Load raw data from a JSON file.

        :param filename: Input JSON file path.
        :type filename: str
        :return: Loaded list of raw entries.
        :rtype: list[dict]
        """
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"Data loaded from {filename}: {len(data)} entries")
            return data
        except (IOError, json.JSONDecodeError) as exc:
            print(f"Error loading data: {exc}")
            return []

    def get_data_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate statistics from cleaned data.

        :param data: List of cleaned entries.
        :type data: list[dict]
        :return: Dictionary of statistics (counts, unique values, etc.).
        :rtype: dict
        """
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
            "unique_programs": len(
                set(entry.get("program", "").lower() for entry in data if entry.get("program"))
            ),
            "unique_schools": len(
                set(entry.get("school", "").lower() for entry in data if entry.get("school"))
            ),
        }

        return stats


def main():
    """
    Command-line entry point to clean and deduplicate Grad Cafe scraped data.

    This command:
      1) Loads raw JSON data
      2) Cleans and normalizes fields
      3) Removes duplicates
      4) Saves cleaned JSON
      5) Prints summary statistics

    :param --input: Input JSON file containing raw scraped entries.
    :type --input: str
    :param --output: Output JSON file path for cleaned entries.
    :type --output: str
    :return: None
    :rtype: None
    """
    # pylint: disable=import-outside-toplevel
    import argparse

    # Add command line argument support
    parser = argparse.ArgumentParser(description="Clean Grad Cafe scraped data")
    parser.add_argument(
        "--input",
        default="applicant_data.json",
        help="Input JSON file (default: applicant_data.json)",
    )
    parser.add_argument(
        "--output",
        default="cleaned_applicant_data.json",
        help="Output JSON file (default: cleaned_applicant_data.json)",
    )

    args = parser.parse_args()

    cleaner = GradCafeDataCleaner()

    # Load raw data from specified input file
    raw_data = cleaner.load_data(args.input)

    if not raw_data:
        print(f"No data found to clean in {args.input}. Please check the file exists.")
        return

    # Clean the data
    cleaned_data = cleaner.clean_data(raw_data)

    # Remove duplicates
    unique_data = cleaner.remove_duplicates(cleaned_data)

    # Save cleaned data to specified output file
    cleaner.save_data(unique_data, args.output)

    # Print statistics
    stats = cleaner.get_data_statistics(unique_data)
    print("\nData Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print(f"\nData cleaning complete! {len(unique_data)} entries ready for LLM processing.")
    print(f"Cleaned data saved to: {args.output}")


if __name__ == "__main__":
    main()
