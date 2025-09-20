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
    """
    Run predefined SQL analytics queries on Grad Café data.

    Manages a DB connection and builds a ``results`` dictionary keyed by query name,
    with each value containing a ``description``, the SQL ``query``, and the ``result``.
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize the query analyzer.

        :param db_config: Connection parameters (``host``, ``port``, ``dbname``, ``user``, ``password``).
        :type db_config: dict
        """
        self.db_config = db_config
        self.connection = None
        self.results = {}
        
    def connect_to_database(self) -> bool:
        """
        Establish a connection to PostgreSQL.

        :return: True if connected successfully, otherwise False.
        :rtype: bool
        """
        try:
            self.connection = psycopg.connect(**self.db_config)
            print("Successfully connected to PostgreSQL database")
            return True
        except psycopg.Error as e:
            print(f"Failed to connect to database: {e}")
            return False
    
    def execute_query(self, query_name: str, query: str, description: str) -> Any:
        """
        Execute a SQL query and store the first row's first column (or row) in ``results``.

        The stored entry has the shape:
        ``results[query_name] = {"description": str, "query": str, "result": Any}``.

        :param query_name: Stable key under which to store the result.
        :type query_name: str
        :param query: SQL string to execute.
        :type query: str
        :param description: Human-readable description of the query.
        :type description: str
        :return: The scalar value (if single column) or the raw row/None.
        :rtype: Any
        """
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
        """
        Q1: Count entries who applied for Fall 2025.

        :return: Integer count.
        :rtype: int | None
        """
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
        """
        Q2: Percentage of entries from international students.

        Includes rows where ``us_or_international`` is non-empty. Rounded to 2 decimals.

        :return: Percentage value (e.g., 42.33).
        :rtype: float | None
        """
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
        """
        Q3: Average GPA, GRE, GRE V, GRE AW for applicants who provided them.

        Applies sanity caps (GRE≤170, GRE V≤170, GRE AW≤6) and rounds to 2 decimals.

        :return: Row with ``(avg_gpa, avg_gre, avg_gre_v, avg_gre_aw)``.
        :rtype: tuple | None
        """
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
        """
        Q4: Average GPA of American students in Fall 2025.

        :return: Average GPA rounded to 2 decimals.
        :rtype: float | None
        """
        query = """
        SELECT ROUND(AVG(gpa)::numeric, 2) as avg_american_gpa_fall_2025
        FROM applicant_data 
        WHERE term ILIKE '%Fall 2025%' 
        AND us_or_international ILIKE '%American%'
        AND gpa IS NOT NULL
        """
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
        """
        Q5: Percentage of Fall 2025 entries that are acceptances.

        :return: Percentage value rounded to 2 decimals.
        :rtype: float | None
        """
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
        """
        Q6: Average GPA of accepted applicants who applied for Fall 2025.

        :return: Average GPA rounded to 2 decimals.
        :rtype: float | None
        """
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
        """
        Q7: Count of JHU Computer Science Masters applications.

        Matches by program/university name or LLM-generated fields.

        :return: Integer count.
        :rtype: int | None
        """
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
        """
        Q8: 2025 acceptances for Georgetown CS PhD.

        :return: Integer count.
        :rtype: int | None
        """
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
        """
        Q9: Percent of international entries for Penn State in Fall 2025.

        :return: Percentage value rounded to 2 decimals.
        :rtype: float | None
        """
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
        """
        Q10: 2025 acceptances for Penn State.

        :return: Integer count.
        :rtype: int | None
        """
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
        """
        Execute all predefined queries in sequence.

        Populates :pyattr:`results` for each question key.
        :return: None
        :rtype: None
        """
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
        """
        Print a human-readable summary of all stored results.

        :return: None
        :rtype: None
        """
        print("\nSUMMARY REPORT")
        print("=" * 80)
        
        for i, (key, data) in enumerate(self.results.items(), 1):
            print(f"\n{i}. {data['description']}")
            print(f"   Result: {data['result']}")
            
        print("\n" + "=" * 80)
    
    def close_connection(self):
        """
        Close the database connection if open.

        :return: None
        :rtype: None
        """
        if self.connection:
            self.connection.close()
            print("Database connection closed")

def main():
    """
    Command-line entry point to execute all queries and print a summary.

    :return: True on success, False otherwise.
    :rtype: bool
    """
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
