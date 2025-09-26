#!/usr/bin/env python3
"""
query_data.py - SQL Queries for Grad Café Data Analysis.

This script contains SQL queries to answer the programming assignment questions
for Module 3. It connects to the PostgreSQL database and executes queries
to analyze grad school admission data.

Author: Wei Liu
Date: September 2025
"""

import sys
from typing import Any, Dict

import psycopg
from psycopg import sql

# pylint: disable=import-error
from config import DB_CONFIG
# pylint: enable=import-error


class GradCafeQueryAnalyzer:
    """
    Run predefined SQL analytics queries on Grad Café data.

    Manages a DB connection and builds a ``results`` dictionary keyed by query name,
    with each value containing a ``description``, the SQL ``query``, and the ``result``.
    """

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize the query analyzer.

        :param db_config: Connection parameters (``host``, ``port``, ``dbname``,
                          ``user``, ``password``).
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

    def execute_query(self, query_name: str, query: Any, description: str) -> Any:
        """
        Execute a SQL query and store the first row's first column (or row) in ``results``.

        The stored entry has the shape:
        ``results[query_name] = {"description": str, "query": str, "result": Any}``.

        :param query_name: Stable key under which to store the result.
        :type query_name: str
        :param query: SQL composed object or string to execute.
        :type query: Any
        :param description: Human-readable description of the query.
        :type description: str
        :return: The scalar value (if single column) or the raw row/None.
        :rtype: Any
        """
        try:
            # pylint: disable=no-member
            cursor = self.connection.cursor()
            # pylint: enable=no-member
            cursor.execute(query)
            result = cursor.fetchone()

            # Store the query as string for display purposes
            query_str = (query.as_string(self.connection)
                        if hasattr(query, 'as_string') else str(query))

            self.results[query_name] = {
                "description": description,
                "query": query_str,
                "result": result[0] if result and len(result) == 1 else result,
            }

            print(f"{query_name}: {result[0] if result and len(result) == 1 else result}")
            return result[0] if result and len(result) == 1 else result

        except psycopg.Error as exc:
            print(f"Error executing {query_name}: {exc}")
            query_str = (query.as_string(self.connection)
                        if hasattr(query, 'as_string') else str(query))
            self.results[query_name] = {
                "description": description,
                "query": query_str,
                "result": f"Error: {exc}",
            }
            return None

    def question_1_fall_2025_entries(self):
        """
        Q1: Count entries who applied for Fall 2025.

        :return: Integer count.
        :rtype: int | None
        """
        # Compose SQL query with identifiers and limit
        query_sql = sql.SQL("""
        SELECT COUNT(*) 
        FROM {table} 
        WHERE {term_col} ILIKE {term_pattern}
        LIMIT {limit}
        """).format(
            table=sql.Identifier('applicant_data'),
            term_col=sql.Identifier('term'),
            term_pattern=sql.Literal('%Fall 2025%'),
            limit=sql.Literal(1)
        )

        return self.execute_query(
            "Q1_Fall_2025_Entries", query_sql, "Count of entries for Fall 2025 applications"
        )

    def question_2_international_percentage(self):
        """
        Q2: Percentage of entries from international students.

        Includes rows where ``us_or_international`` is non-empty. Rounded to 2 decimals.

        :return: Percentage value (e.g., 42.33).
        :rtype: float | None
        """
        # Compose SQL query with identifiers and limit
        query_sql = sql.SQL("""
        SELECT ROUND(
            (COUNT(*) FILTER (WHERE {us_intl_col} ILIKE {intl_pattern}) * 100.0 / COUNT(*)), 
            2
        ) as international_percentage
        FROM {table} 
        WHERE {us_intl_col} IS NOT NULL 
        AND {us_intl_col} != {empty_str}
        LIMIT {limit}
        """).format(
            table=sql.Identifier('applicant_data'),
            us_intl_col=sql.Identifier('us_or_international'),
            intl_pattern=sql.Literal('%International%'),
            empty_str=sql.Literal(''),
            limit=sql.Literal(1)
        )

        return self.execute_query(
            "Q2_International_Percentage",
            query_sql,
            "Percentage of international students (to 2 decimal places)",
        )

    def question_3_average_metrics(self):
        """
        Q3: Average GPA, GRE, GRE V, GRE AW for applicants who provided them.

        Applies sanity caps (GRE≤170, GRE V≤170, GRE AW≤6) and rounds to 2 decimals.

        :return: Row with ``(avg_gpa, avg_gre, avg_gre_v, avg_gre_aw)``.
        :rtype: tuple | None
        """
        # Compose SQL query with identifiers and limit
        query_sql = sql.SQL("""
        SELECT 
            ROUND(AVG({gpa_col})::numeric, 2) as avg_gpa,
            ROUND(AVG({gre_col})::numeric, 2) as avg_gre,
            ROUND(AVG({gre_v_col})::numeric, 2) as avg_gre_v,
            ROUND(AVG({gre_aw_col})::numeric, 2) as avg_gre_aw
        FROM {table} 
        WHERE ({gpa_col} IS NOT NULL OR {gre_col} IS NOT NULL OR {gre_v_col} IS NOT NULL OR {gre_aw_col} IS NOT NULL)
        AND ({gre_col} IS NULL OR {gre_col} <= {gre_max})
        AND ({gre_v_col} IS NULL OR {gre_v_col} <= {gre_v_max})
        AND ({gre_aw_col} IS NULL OR {gre_aw_col} <= {gre_aw_max})
        LIMIT {limit}
        """).format(
            table=sql.Identifier('applicant_data'),
            gpa_col=sql.Identifier('gpa'),
            gre_col=sql.Identifier('gre'),
            gre_v_col=sql.Identifier('gre_v'),
            gre_aw_col=sql.Identifier('gre_aw'),
            gre_max=sql.Literal(170),
            gre_v_max=sql.Literal(170),
            gre_aw_max=sql.Literal(6),
            limit=sql.Literal(1)
        )

        return self.execute_query(
            "Q3_Average_Metrics",
            query_sql,
            "Average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics "
            "(with realistic score filters)",
        )

    def question_4_american_fall_2025_gpa(self):
        """
        Q4: Average GPA of American students in Fall 2025.

        :return: Average GPA rounded to 2 decimals.
        :rtype: float | None
        """
        # Compose SQL query with identifiers and limit
        query_sql = sql.SQL("""
        SELECT ROUND(AVG({gpa_col})::numeric, 2) as avg_american_gpa_fall_2025
        FROM {table} 
        WHERE {term_col} ILIKE {term_pattern} 
        AND {us_intl_col} ILIKE {american_pattern}
        AND {gpa_col} IS NOT NULL
        LIMIT {limit}
        """).format(
            table=sql.Identifier('applicant_data'),
            gpa_col=sql.Identifier('gpa'),
            term_col=sql.Identifier('term'),
            us_intl_col=sql.Identifier('us_or_international'),
            term_pattern=sql.Literal('%Fall 2025%'),
            american_pattern=sql.Literal('%American%'),
            limit=sql.Literal(1)
        )

        return self.execute_query(
            "Q4_American_Fall_2025_GPA",
            query_sql,
            "Average GPA of American students in Fall 2025",
        )

    def question_5_fall_2025_acceptance_rate(self):
        """
        Q5: Percentage of Fall 2025 entries that are acceptances.

        :return: Percentage value rounded to 2 decimals.
        :rtype: float | None
        """
        # Compose SQL query with identifiers and limit
        query_sql = sql.SQL("""
        SELECT ROUND(
            (COUNT(*) FILTER (WHERE {status_col} ILIKE {accept_pattern}) * 100.0 / COUNT(*)), 
            2
        ) as acceptance_rate_fall_2025
        FROM {table} 
        WHERE {term_col} ILIKE {term_pattern}
        LIMIT {limit}
        """).format(
            table=sql.Identifier('applicant_data'),
            status_col=sql.Identifier('status'),
            term_col=sql.Identifier('term'),
            accept_pattern=sql.Literal('%Accept%'),
            term_pattern=sql.Literal('%Fall 2025%'),
            limit=sql.Literal(1)
        )

        return self.execute_query(
            "Q5_Fall_2025_Acceptance_Rate",
            query_sql,
            "Percentage of Fall 2025 entries that are acceptances (to 2 decimal places)",
        )

    def question_6_fall_2025_accepted_gpa(self):
        """
        Q6: Average GPA of accepted applicants who applied for Fall 2025.

        :return: Average GPA rounded to 2 decimals.
        :rtype: float | None
        """
        # Compose SQL query with identifiers and limit
        query_sql = sql.SQL("""
        SELECT ROUND(AVG({gpa_col})::numeric, 2) as avg_gpa_accepted_fall_2025
        FROM {table} 
        WHERE {term_col} ILIKE {term_pattern} 
        AND {status_col} ILIKE {accept_pattern}
        AND {gpa_col} IS NOT NULL
        LIMIT {limit}
        """).format(
            table=sql.Identifier('applicant_data'),
            gpa_col=sql.Identifier('gpa'),
            term_col=sql.Identifier('term'),
            status_col=sql.Identifier('status'),
            term_pattern=sql.Literal('%Fall 2025%'),
            accept_pattern=sql.Literal('%Accept%'),
            limit=sql.Literal(1)
        )

        return self.execute_query(
            "Q6_Fall_2025_Accepted_GPA",
            query_sql,
            "Average GPA of accepted applicants for Fall 2025",
        )

    def question_7_jhu_cs_masters(self):
        """
        Q7: Count of JHU Computer Science Masters applications.

        Matches by program/university name or LLM-generated fields.

        :return: Integer count.
        :rtype: int | None
        """
        # Compose SQL query with identifiers and limit
        query_sql = sql.SQL("""
        SELECT COUNT(*) 
        FROM {table} 
        WHERE (
            {program_col} ILIKE {jh_pattern} OR 
            {program_col} ILIKE {jhu_pattern} OR
            {llm_univ_col} ILIKE {jh_pattern}
        )
        AND (
            {program_col} ILIKE {cs_pattern} OR 
            {program_col} ILIKE {cs_abbr_pattern} OR
            {llm_prog_col} ILIKE {cs_pattern}
        )
        AND {degree_col} ILIKE {masters_pattern}
        LIMIT {limit}
        """).format(
            table=sql.Identifier('applicant_data'),
            program_col=sql.Identifier('program'),
            llm_univ_col=sql.Identifier('llm_generated_university'),
            llm_prog_col=sql.Identifier('llm_generated_program'),
            degree_col=sql.Identifier('degree'),
            jh_pattern=sql.Literal('%Johns Hopkins%'),
            jhu_pattern=sql.Literal('%JHU%'),
            cs_pattern=sql.Literal('%Computer Science%'),
            cs_abbr_pattern=sql.Literal('%CS%'),
            masters_pattern=sql.Literal('%Masters%'),
            limit=sql.Literal(1)
        )

        return self.execute_query(
            "Q7_JHU_CS_Masters",
            query_sql,
            "Count of JHU Computer Science Masters applications",
        )

    def question_8_georgetown_cs_phd_2025_acceptances(self):
        """
        Q8: 2025 acceptances for Georgetown CS PhD.

        :return: Integer count.
        :rtype: int | None
        """
        # Compose SQL query with identifiers and limit
        query_sql = sql.SQL("""
        SELECT COUNT(*) 
        FROM {table} 
        WHERE (
            {program_col} ILIKE {georgetown_pattern} OR
            {llm_univ_col} ILIKE {georgetown_pattern}
        )
        AND (
            {program_col} ILIKE {cs_pattern} OR 
            {program_col} ILIKE {cs_abbr_pattern} OR
            {llm_prog_col} ILIKE {cs_pattern}
        )
        AND {degree_col} ILIKE {phd_pattern}
        AND {status_col} ILIKE {accept_pattern}
        AND {date_col} >= {date_2025}
        LIMIT {limit}
        """).format(
            table=sql.Identifier('applicant_data'),
            program_col=sql.Identifier('program'),
            llm_univ_col=sql.Identifier('llm_generated_university'),
            llm_prog_col=sql.Identifier('llm_generated_program'),
            degree_col=sql.Identifier('degree'),
            status_col=sql.Identifier('status'),
            date_col=sql.Identifier('date_added'),
            georgetown_pattern=sql.Literal('%Georgetown%'),
            cs_pattern=sql.Literal('%Computer Science%'),
            cs_abbr_pattern=sql.Literal('%CS%'),
            phd_pattern=sql.Literal('%PhD%'),
            accept_pattern=sql.Literal('%Accept%'),
            date_2025=sql.Literal('2025-01-01'),
            limit=sql.Literal(1)
        )

        return self.execute_query(
            "Q8_Georgetown_CS_PhD_2025_Acceptances",
            query_sql,
            "Count of 2025 Georgetown CS PhD acceptances",
        )

    def question_9_penn_state_international_fall_2025(self):
        """
        Q9: Percent of international entries for Penn State in Fall 2025.

        :return: Percentage value rounded to 2 decimals.
        :rtype: float | None
        """
        # Compose SQL query with identifiers and limit
        query_sql = sql.SQL("""
        SELECT ROUND(
            (COUNT(*) FILTER (WHERE {us_intl_col} ILIKE {intl_pattern}) * 100.0 / COUNT(*)), 
            2
        ) as penn_state_international_percentage_fall_2025
        FROM {table} 
        WHERE {term_col} ILIKE {term_pattern}
        AND (
            {program_col} ILIKE {penn_state_pattern} OR 
            {program_col} ILIKE {penn_state_short} OR
            {program_col} ILIKE {psu_pattern} OR
            {llm_univ_col} ILIKE {penn_state_pattern} OR
            {llm_univ_col} ILIKE {penn_state_short}
        )
        AND {us_intl_col} IS NOT NULL 
        AND {us_intl_col} != {empty_str}
        LIMIT {limit}
        """).format(
            table=sql.Identifier('applicant_data'),
            us_intl_col=sql.Identifier('us_or_international'),
            term_col=sql.Identifier('term'),
            program_col=sql.Identifier('program'),
            llm_univ_col=sql.Identifier('llm_generated_university'),
            intl_pattern=sql.Literal('%International%'),
            term_pattern=sql.Literal('%Fall 2025%'),
            penn_state_pattern=sql.Literal('%Pennsylvania State%'),
            penn_state_short=sql.Literal('%Penn State%'),
            psu_pattern=sql.Literal('%PSU%'),
            empty_str=sql.Literal(''),
            limit=sql.Literal(1)
        )

        return self.execute_query(
            "Q9_Penn_State_International_Fall_2025",
            query_sql,
            "Percentage of international students at Penn State for Fall 2025",
        )

    def question_10_penn_state_2025_acceptances(self):
        """
        Q10: 2025 acceptances for Penn State.

        :return: Integer count.
        :rtype: int | None
        """
        # Compose SQL query with identifiers and limit
        query_sql = sql.SQL("""
        SELECT COUNT(*) 
        FROM {table} 
        WHERE (
            {program_col} ILIKE {penn_state_pattern} OR 
            {program_col} ILIKE {penn_state_short} OR
            {program_col} ILIKE {psu_pattern} OR
            {llm_univ_col} ILIKE {penn_state_pattern} OR
            {llm_univ_col} ILIKE {penn_state_short}
        )
        AND {status_col} ILIKE {accept_pattern}
        AND {date_col} >= {date_2025}
        LIMIT {limit}
        """).format(
            table=sql.Identifier('applicant_data'),
            program_col=sql.Identifier('program'),
            llm_univ_col=sql.Identifier('llm_generated_university'),
            status_col=sql.Identifier('status'),
            date_col=sql.Identifier('date_added'),
            penn_state_pattern=sql.Literal('%Pennsylvania State%'),
            penn_state_short=sql.Literal('%Penn State%'),
            psu_pattern=sql.Literal('%PSU%'),
            accept_pattern=sql.Literal('%Accept%'),
            date_2025=sql.Literal('2025-01-01'),
            limit=sql.Literal(1)
        )

        return self.execute_query(
            "Q10_Penn_State_2025_Acceptances",
            query_sql,
            "Count of 2025 acceptances for Penn State",
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

        for i, (_, data) in enumerate(self.results.items(), 1):
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
            # pylint: disable=no-member
            self.connection.close()
            # pylint: enable=no-member
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

    except (psycopg.Error, KeyError) as exc:
        print(f"Unexpected error: {exc}")
        return False

    finally:
        analyzer.close_connection()


if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)
