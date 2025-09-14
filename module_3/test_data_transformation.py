#!/usr/bin/env python3
"""
test_data_transformation.py - Test the data transformation logic

This script tests the data transformation from JSONL format to database format
without requiring a database connection.
"""

import json
import sys
from datetime import datetime
from dateutil import parser as date_parser

def parse_date(date_string: str):
    """Parse date string into datetime object"""
    if not date_string:
        return None
    
    try:
        return date_parser.parse(date_string).date()
    except (ValueError, TypeError) as e:
        print(f"Warning: Failed to parse date '{date_string}': {e}")
        return None

def parse_float(value):
    """Parse value into float, handling None and string values"""
    if value is None or value == '':
        return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        print(f"Warning: Failed to parse float value '{value}'")
        return None

def transform_record(record):
    """Transform a JSONL record into database format"""
    # Map JSONL fields to database schema
    program = record.get('program', '')
    comments = record.get('comments', '')
    date_added = parse_date(record.get('date_added', ''))
    url = record.get('url', '')
    status = record.get('status', '')
    term = record.get('semester', '')  # semester maps to term
    us_or_international = record.get('applicant_type', '')
    gpa = parse_float(record.get('gpa'))
    gre = parse_float(record.get('gre_quant'))  # gre_quant maps to gre
    gre_v = parse_float(record.get('gre_verbal'))
    gre_aw = parse_float(record.get('gre_aw'))
    degree = record.get('degree', '')
    llm_generated_program = record.get('llm-generated-program', '')
    llm_generated_university = record.get('llm-generated-university', '')
    
    return {
        'program': program,
        'comments': comments,
        'date_added': date_added,
        'url': url,
        'status': status,
        'term': term,
        'us_or_international': us_or_international,
        'gpa': gpa,
        'gre': gre,
        'gre_v': gre_v,
        'gre_aw': gre_aw,
        'degree': degree,
        'llm_generated_program': llm_generated_program,
        'llm_generated_university': llm_generated_university
    }

def main():
    """Test the data transformation with sample records"""
    print("Testing data transformation logic...")
    print("=" * 50)
    
    try:
        with open('llm_extend_applicant_data.jsonl', 'r', encoding='utf-8') as file:
            for i, line in enumerate(file):
                if i >= 5:  # Test first 5 records
                    break
                
                try:
                    record = json.loads(line.strip())
                    transformed = transform_record(record)
                    
                    print(f"\nRecord {i + 1}:")
                    print(f"  Original program: {record.get('program', 'N/A')}")
                    print(f"  Transformed program: {transformed['program']}")
                    print(f"  Original date_added: {record.get('date_added', 'N/A')}")
                    print(f"  Transformed date_added: {transformed['date_added']}")
                    print(f"  Original gpa: {record.get('gpa', 'N/A')}")
                    print(f"  Transformed gpa: {transformed['gpa']}")
                    print(f"  Original gre_quant: {record.get('gre_quant', 'N/A')}")
                    print(f"  Transformed gre: {transformed['gre']}")
                    print(f"  Status: {transformed['status']}")
                    print(f"  Degree: {transformed['degree']}")
                    print(f"  LLM Program: {transformed['llm_generated_program']}")
                    print(f"  LLM University: {transformed['llm_generated_university']}")
                    
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON on line {i + 1}: {e}")
                except Exception as e:
                    print(f"Error processing record {i + 1}: {e}")
        
        print("\n" + "=" * 50)
        print("Data transformation test completed successfully!")
        
    except FileNotFoundError:
        print("Error: llm_extend_applicant_data.jsonl not found")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
