#!/usr/bin/env python3
"""
query_data.py - SQL Queries for Grad Café Data Analysis

This script contains SQL queries to answer the programming assignment questions
for Module 3. It connects to the PostgreSQL database and executes queries
to analyze grad school admission data.

Author: Wei Liu
Date: September 2025
"""

import psycopg
import sys
from typing import Dict, Any

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'gradcafe_db',
    'user': 'momo',
    'password': ''
}

class GradCafeQueryAnalyzer:
    """Class to handle SQL queries for grad café data analysis"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """Initialize the query analyzer with database configuration"""
        self.db_config = db_config
        self.connection = None
        self.results = {}
        
    def connect_to_database(self) -> bool:
        """Establish connection to PostgreSQL database"""
        try:
            self.connection = psycopg.connect(**self.db_config)
            print("Successfully connected to PostgreSQL database")
            return True
        except psycopg.Error as e:
            print(f"Failed to connect to database: {e}")
            return False
    
    def execute_query(self, query_name: str, query: str, description: str) -> Any:
        """Execute a SQL query and store the result"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                
                self.results[query_name] = {
                    'description': description,
                    'query': query,
                    'result': result[0] if result and len(result) == 1 else result
                }
                
                print(f"{query_name}: {result[0] if result and len(result) == 1 else result}")
                return result[0] if result and len(result) == 1 else result
                
        except psycopg.Error as e:
            print(f"Error executing {query_name}: {e}")
            self.results[query_name] = {
                'description': description,
                'query': query,
                'result': f"Error: {e}"
            }
            return None
    
    def question_1_fall_2025_entries(self):
        """Q1: How many entries do you have in your database who have applied for Fall 2025?"""
        query = """
        SELECT COUNT(*) 
        FROM applicant_data 
        WHERE term ILIKE '%Fall 2025%'
        """
        
        return self.execute_query(
            "Q1_Fall_2025_Entries",
            query,
            "Count of entries for Fall 2025 applications"
        )
    
    def question_2_international_percentage(self):
        """Q2: What percentage of entries are from international students (not American or Other)?"""
        query = """
        SELECT ROUND(
            (COUNT(*) FILTER (WHERE us_or_international ILIKE '%International%') * 100.0 / COUNT(*)), 
            2
        ) as international_percentage
        FROM applicant_data 
        WHERE us_or_international IS NOT NULL 
        AND us_or_international != ''
        """
        
        return self.execute_query(
            "Q2_International_Percentage",
            query,
            "Percentage of international students (to 2 decimal places)"
        )
    
    def question_3_average_metrics(self):
        """Q3: What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?"""
        query = """
        SELECT 
            ROUND(AVG(gpa)::numeric, 2) as avg_gpa,
            ROUND(AVG(gre)::numeric, 2) as avg_gre,
            ROUND(AVG(gre_v)::numeric, 2) as avg_gre_v,
            ROUND(AVG(gre_aw)::numeric, 2) as avg_gre_aw
        FROM applicant_data 
        WHERE (gpa IS NOT NULL OR gre IS NOT NULL OR gre_v IS NOT NULL OR gre_aw IS NOT NULL)
        AND (gre IS NULL OR gre <= 170)
        AND (gre_v IS NULL OR gre_v <= 170)
        AND (gre_aw IS NULL OR gre_aw <= 6)
        """
        
        return self.execute_query(
            "Q3_Average_Metrics",
            query,
            "Average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics (with realistic score filters)"
        )
    
    def question_4_american_fall_2025_gpa(self):
        """Q4: What is their average GPA of American students in Fall 2025?"""
        query = """
        SELECT ROUND(AVG(gpa)::numeric, 2) as avg_american_gpa_fall_2025
        FROM applicant_data 
        WHERE term ILIKE '%Fall 2025%' 
        AND us_or_international ILIKE '%American%'
        AND gpa IS NOT NULL
        """
        
        return self.execute_query(
            "Q4_American_Fall_2025_GPA",
            query,
            "Average GPA of American students in Fall 2025"
        )
    
    def question_5_fall_2025_acceptance_rate(self):
        """Q5: What percent of entries for Fall 2025 are Acceptances?"""
        query = """
        SELECT ROUND(
            (COUNT(*) FILTER (WHERE status ILIKE '%Accept%') * 100.0 / COUNT(*)), 
            2
        ) as acceptance_rate_fall_2025
        FROM applicant_data 
        WHERE term ILIKE '%Fall 2025%'
        """
        
        return self.execute_query(
            "Q5_Fall_2025_Acceptance_Rate",
            query,
            "Percentage of Fall 2025 entries that are acceptances (to 2 decimal places)"
        )
    
    def question_6_fall_2025_accepted_gpa(self):
        """Q6: What is the average GPA of applicants who applied for Fall 2025 who are Acceptances?"""
        query = """
        SELECT ROUND(AVG(gpa)::numeric, 2) as avg_gpa_accepted_fall_2025
        FROM applicant_data 
        WHERE term ILIKE '%Fall 2025%' 
        AND status ILIKE '%Accept%'
        AND gpa IS NOT NULL
        """
        
        return self.execute_query(
            "Q6_Fall_2025_Accepted_GPA",
            query,
            "Average GPA of accepted applicants for Fall 2025"
        )
    
    def question_7_jhu_cs_masters(self):
        """Q7: How many entries are from applicants who applied to JHU for a masters degrees in Computer Science?"""
        query = """
        SELECT COUNT(*) 
        FROM applicant_data 
        WHERE (
            program ILIKE '%Johns Hopkins%' OR 
            program ILIKE '%JHU%' OR
            llm_generated_university ILIKE '%Johns Hopkins%'
        )
        AND (
            program ILIKE '%Computer Science%' OR 
            program ILIKE '%CS%' OR
            llm_generated_program ILIKE '%Computer Science%'
        )
        AND degree ILIKE '%Masters%'
        """
        
        return self.execute_query(
            "Q7_JHU_CS_Masters",
            query,
            "Count of JHU Computer Science Masters applications"
        )
    
    def question_8_georgetown_cs_phd_2025_acceptances(self):
        """Q8: How many entries from 2025 are acceptances from applicants who applied to Georgetown University for a PhD in Computer Science?"""
        query = """
        SELECT COUNT(*) 
        FROM applicant_data 
        WHERE (
            program ILIKE '%Georgetown%' OR
            llm_generated_university ILIKE '%Georgetown%'
        )
        AND (
            program ILIKE '%Computer Science%' OR 
            program ILIKE '%CS%' OR
            llm_generated_program ILIKE '%Computer Science%'
        )
        AND degree ILIKE '%PhD%'
        AND status ILIKE '%Accept%'
        AND date_added >= '2025-01-01'
        """
        
        return self.execute_query(
            "Q8_Georgetown_CS_PhD_2025_Acceptances",
            query,
            "Count of 2025 Georgetown CS PhD acceptances"
        )
    
    def question_9_penn_state_international_fall_2025(self):
        """Q9: Pennsylvania State University International Student Percentage for Fall 2025"""
        query = """
        SELECT ROUND(
            (COUNT(*) FILTER (WHERE us_or_international ILIKE '%International%') * 100.0 / COUNT(*)), 
            2
        ) as penn_state_international_percentage_fall_2025
        FROM applicant_data 
        WHERE term ILIKE '%Fall 2025%'
        AND (
            program ILIKE '%Pennsylvania State%' OR 
            program ILIKE '%Penn State%' OR
            program ILIKE '%PSU%' OR
            llm_generated_university ILIKE '%Pennsylvania State%' OR
            llm_generated_university ILIKE '%Penn State%'
        )
        AND us_or_international IS NOT NULL 
        AND us_or_international != ''
        """
        
        return self.execute_query(
            "Q9_Penn_State_International_Fall_2025",
            query,
            "Percentage of international students at Penn State for Fall 2025"
        )
    
    def question_10_penn_state_2025_acceptances(self):
        """Q10: Pennsylvania State University Fall 2025 Acceptances"""
        query = """
        SELECT COUNT(*) 
        FROM applicant_data 
        WHERE (
            program ILIKE '%Pennsylvania State%' OR 
            program ILIKE '%Penn State%' OR
            program ILIKE '%PSU%' OR
            llm_generated_university ILIKE '%Pennsylvania State%' OR
            llm_generated_university ILIKE '%Penn State%'
        )
        AND status ILIKE '%Accept%'
        AND date_added >= '2025-01-01'
        """
        
        return self.execute_query(
            "Q10_Penn_State_2025_Acceptances",
            query,
            "Count of 2025 acceptances for Penn State"
        )
    
    def run_all_queries(self):
        """Execute all queries in sequence"""
        print("Starting Grad Café Data Analysis")
        print("=" * 60)
        
        # Execute all queries
        self.question_1_fall_2025_entries()
        self.question_2_international_percentage()
        self.question_3_average_metrics()
        self.question_4_american_fall_2025_gpa()
        self.question_5_fall_2025_acceptance_rate()
        self.question_6_fall_2025_accepted_gpa()
        self.question_7_jhu_cs_masters()
        self.question_8_georgetown_cs_phd_2025_acceptances()
        self.question_9_penn_state_international_fall_2025()
        self.question_10_penn_state_2025_acceptances()
        
        print("\n" + "=" * 60)
        print("Analysis Complete!")
        
    def print_summary_report(self):
        """Print a formatted summary of all results"""
        print("\nSUMMARY REPORT")
        print("=" * 80)
        
        for i, (key, data) in enumerate(self.results.items(), 1):
            print(f"\n{i}. {data['description']}")
            print(f"   Result: {data['result']}")
            
        print("\n" + "=" * 80)
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")

def main():
    """Main function to execute all queries"""
    analyzer = GradCafeQueryAnalyzer(DB_CONFIG)
    
    try:
        # Connect to database
        if not analyzer.connect_to_database():
            return False
        
        # Run all queries
        analyzer.run_all_queries()
        
        # Print summary report
        analyzer.print_summary_report()
        
        return True
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    finally:
        analyzer.close_connection()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
