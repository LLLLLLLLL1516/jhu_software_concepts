#!/usr/bin/env python3
"""
load_data.py - Load grad café data into PostgreSQL database.

This script loads the cleaned and LLM-extended grad café data from
llm_extend_applicant_data.jsonl into a PostgreSQL database.

Author: Wei Liu
Date: September 2025
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import psycopg
from psycopg import sql
from dateutil import parser as date_parser

# pylint: disable=import-error
from config import DB_CONFIG
# pylint: enable=import-error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("load_data.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Table schema definition
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS applicant_data (
    p_id SERIAL PRIMARY KEY,
    program TEXT,
    comments TEXT,
    date_added DATE,
    url TEXT,
    status TEXT,
    term TEXT,
    us_or_international TEXT,
    gpa FLOAT,
    gre FLOAT,
    gre_v FLOAT,
    gre_aw FLOAT,
    degree TEXT,
    llm_generated_program TEXT,
    llm_generated_university TEXT
);
"""


class GradCafeDataLoader:
    """
    Handle loading Grad Café data into PostgreSQL.

    Provides connection management, table creation, record transformation,
    batch inserts from JSONL, and table statistics.
    """

    def __init__(self, db_config: Dict[str, Any]):
        """
        Initialize the data loader.

        :param db_config: Database configuration dictionary containing keys
                          ``host``, ``port``, ``dbname``, ``user``, ``password``.
        :type db_config: dict
        """
        self.db_config = db_config
        self.connection = None

    def connect_to_database(self) -> bool:
        """
        Establish a connection to the PostgreSQL database.

        :return: True if connected successfully, otherwise False.
        :rtype: bool
        """
        try:
            self.connection = psycopg.connect(**self.db_config)
            logger.info("Successfully connected to PostgreSQL database")
            return True
        except psycopg.Error as exc:
            logger.error("Failed to connect to database: %s", exc)
            return False

    def create_table(self) -> bool:
        """
        Create the ``applicant_data`` table if it does not exist.

        :return: True if the table exists or was created successfully, False on error.
        :rtype: bool
        """
        try:
            # pylint: disable=no-member
            cursor = self.connection.cursor()
            cursor.execute(CREATE_TABLE_SQL)
            self.connection.commit()
            # pylint: enable=no-member
            logger.info("Table 'applicant_data' created or already exists")
            return True
        except psycopg.Error as exc:
            logger.error("Failed to create table: %s", exc)
            return False

    def parse_date(self, date_string: str) -> Optional[datetime]:
        """
        Parse a date string into a ``date`` value.

        Uses ``dateutil.parser.parse`` to accept multiple formats.

        :param date_string: Date string to parse (e.g., ``"2024-01-15"``).
        :type date_string: str
        :return: Parsed date value, or None if parsing fails/empty.
        :rtype: Optional[datetime.date]
        """
        if not date_string:
            return None

        try:
            # Handle various date formats
            return date_parser.parse(date_string).date()
        except (ValueError, TypeError) as exc:
            logger.warning("Failed to parse date '%s': %s", date_string, exc)
            return None

    def parse_float(self, value: Any) -> Optional[float]:
        """
        Convert a value to a float if possible.

        :param value: Numeric/str value to convert (e.g., ``"3.85"``).
        :type value: Any
        :return: Float value or None if conversion fails/empty.
        :rtype: Optional[float]
        """
        if value is None or value == "":
            return None

        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning("Failed to parse float value '%s'", value)
            return None

    def transform_record(self, record: Dict[str, Any]) -> Tuple[Any, ...]:
        """
        Transform a JSONL record into a tuple matching the DB schema.

        Maps JSON fields to columns of ``applicant_data`` and applies parsing for
        date/float fields.

        :param record: A single JSON object (one line from the JSONL file).
        :type record: dict
        :return: Tuple of values in the order expected by the insert statement.
        :rtype: tuple
        """
        # Map JSONL fields to database schema
        gre_total = self.parse_float(record.get("gre_total"))
        gre_quant = self.parse_float(record.get("gre_quant"))
        gre = gre_total or gre_quant

        return (
            record.get("program", ""),
            record.get("comments", ""),
            self.parse_date(record.get("date_added", "")),
            record.get("url", ""),
            record.get("status", ""),
            record.get("semester", ""),  # semester maps to term
            record.get("applicant_type", ""),
            self.parse_float(record.get("gpa")),
            gre,
            self.parse_float(record.get("gre_verbal")),
            self.parse_float(record.get("gre_aw")),
            record.get("degree", ""),
            record.get("llm-generated-program", ""),
            record.get("llm-generated-university", ""),
        )

    def load_data_from_jsonl(self, file_path: str, batch_size: int = 1000) -> bool:
        """
        Load data lines from a JSONL file and insert into the database in batches.

        Each line is parsed as JSON, transformed to match the DB schema, and inserted
        using ``executemany`` in chunks.

        :param file_path: Path to the input JSONL file.
        :type file_path: str
        :param batch_size: Number of rows per batch insert (default: 1000).
        :type batch_size: int
        :return: True if at least one record was inserted, False otherwise.
        :rtype: bool
        :raises FileNotFoundError: If the input file does not exist.
        """
        try:
            insert_sql = """
            INSERT INTO applicant_data (
                program, comments, date_added, url, status, term,
                us_or_international, gpa, gre, gre_v, gre_aw, degree,
                llm_generated_program, llm_generated_university
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            batch_data = []
            total_records = 0
            successful_inserts = 0

            logger.info("Starting to load data from %s", file_path)

            with open(file_path, "r", encoding="utf-8") as file:
                for line_num, line in enumerate(file, 1):
                    try:
                        # Parse JSON line
                        record = json.loads(line.strip())
                        total_records += 1

                        # Transform record
                        transformed_record = self.transform_record(record)
                        batch_data.append(transformed_record)

                        # Insert batch when batch_size is reached
                        if len(batch_data) >= batch_size:
                            inserted = self._insert_batch(insert_sql, batch_data)
                            successful_inserts += inserted
                            batch_data = []

                            if total_records % (batch_size * 10) == 0:
                                logger.info(
                                    "Processed %d records, inserted %d successfully",
                                    total_records,
                                    successful_inserts
                                )

                    except json.JSONDecodeError as exc:
                        logger.warning("Failed to parse JSON on line %d: %s", line_num, exc)
                        continue
                    except (KeyError, TypeError, ValueError) as exc:
                        logger.warning("Error processing line %d: %s", line_num, exc)
                        continue

                # Insert remaining records in batch
                if batch_data:
                    inserted = self._insert_batch(insert_sql, batch_data)
                    successful_inserts += inserted

            logger.info(
                "Data loading completed. Total records processed: %d, "
                "Successfully inserted: %d",
                total_records,
                successful_inserts
            )

            return successful_inserts > 0

        except FileNotFoundError:
            logger.error("File not found: %s", file_path)
            return False
        except IOError as exc:
            logger.error("Unexpected error during data loading: %s", exc)
            return False

    def _insert_batch(self, insert_sql: str, batch_data: List[Tuple]) -> int:
        """
        Insert a batch of records into the database.

        :param insert_sql: Parameterized INSERT SQL statement.
        :type insert_sql: str
        :param batch_data: List of tuples to insert.
        :type batch_data: list[tuple]
        :return: Number of records inserted (len(batch_data)) on success, 0 on failure.
        :rtype: int
        """
        try:
            # pylint: disable=no-member
            cursor = self.connection.cursor()
            cursor.executemany(insert_sql, batch_data)
            self.connection.commit()
            # pylint: enable=no-member
            return len(batch_data)
        except psycopg.Error as exc:
            logger.error("Failed to insert batch: %s", exc)
            # pylint: disable=no-member
            self.connection.rollback()
            # pylint: enable=no-member
            return 0

    def get_table_stats(self) -> Dict[str, Any]:
        """
        Compute basic statistics for the ``applicant_data`` table.

        Statistics include total row count, per-status distribution, and per-degree
        distribution (non-empty values only).

        :return: Dictionary with statistics keys: ``total_records``,
                 ``status_distribution``, ``degree_distribution``.
        :rtype: dict
        """
        try:
            # pylint: disable=no-member
            cursor = self.connection.cursor()
            # pylint: enable=no-member

            # Total count query with SQL composition
            count_query = sql.SQL("SELECT COUNT(*) FROM {table} LIMIT {limit}").format(
                table=sql.Identifier('applicant_data'),
                limit=sql.Literal(1)
            )
            cursor.execute(count_query)
            total_count = cursor.fetchone()[0]

            # Status distribution query with SQL composition
            status_query = sql.SQL("""
                SELECT {status_col}, COUNT(*)
                FROM {table}
                WHERE {status_col} IS NOT NULL AND {status_col} != {empty_str}
                GROUP BY {status_col}
                ORDER BY COUNT(*) DESC
                LIMIT {limit}
            """).format(
                table=sql.Identifier('applicant_data'),
                status_col=sql.Identifier('status'),
                empty_str=sql.Literal(''),
                limit=sql.Literal(100)  # Reasonable limit for distribution
            )
            cursor.execute(status_query)
            status_dist = cursor.fetchall()

            # Degree distribution query with SQL composition
            degree_query = sql.SQL("""
                SELECT {degree_col}, COUNT(*)
                FROM {table}
                WHERE {degree_col} IS NOT NULL AND {degree_col} != {empty_str}
                GROUP BY {degree_col}
                ORDER BY COUNT(*) DESC
                LIMIT {limit}
            """).format(
                table=sql.Identifier('applicant_data'),
                degree_col=sql.Identifier('degree'),
                empty_str=sql.Literal(''),
                limit=sql.Literal(100)  # Reasonable limit for distribution
            )
            cursor.execute(degree_query)
            degree_dist = cursor.fetchall()

            return {
                "total_records": total_count,
                "status_distribution": status_dist,
                "degree_distribution": degree_dist,
            }
        except psycopg.Error as exc:
            logger.error("Failed to get table statistics: %s", exc)
            return {}

    def close_connection(self):
        """
        Close the database connection.

        :return: None
        :rtype: None
        """
        if self.connection:
            # pylint: disable=no-member
            self.connection.close()
            # pylint: enable=no-member
            logger.info("Database connection closed")


def main():
    """
    Execute the data loading process from the command line.

    Steps:
      1) Connect to the database
      2) Create the target table if needed
      3) Load JSONL data with batch inserts
      4) Print basic statistics

    :return: True if the load succeeded, False otherwise.
    :rtype: bool
    """
    # pylint: disable=import-outside-toplevel
    import argparse

    # Add command line argument support
    parser = argparse.ArgumentParser(description="Load Grad Cafe data into PostgreSQL")
    parser.add_argument(
        "--input",
        default="llm_extend_applicant_data.jsonl",
        help="Input JSONL file (default: llm_extend_applicant_data.jsonl)",
    )

    args = parser.parse_args()

    logger.info("Starting grad cafe data loading process")

    # Initialize data loader
    loader = GradCafeDataLoader(DB_CONFIG)

    try:
        # Connect to database
        if not loader.connect_to_database():
            logger.error("Failed to connect to database. Exiting.")
            return False

        # Create table
        if not loader.create_table():
            logger.error("Failed to create table. Exiting.")
            return False

        # Load data from specified file
        jsonl_file = args.input
        if not loader.load_data_from_jsonl(jsonl_file):
            logger.error("Failed to load data. Exiting.")
            return False

        # Display statistics
        stats = loader.get_table_stats()
        if stats:
            logger.info("Data loading completed successfully!")
            logger.info("Total records loaded: %d", stats['total_records'])

            if stats["status_distribution"]:
                logger.info("Status distribution:")
                for status, count in stats["status_distribution"][:5]:  # Top 5
                    logger.info("  %s: %d", status, count)

            if stats["degree_distribution"]:
                logger.info("Degree distribution:")
                for degree, count in stats["degree_distribution"]:
                    logger.info("  %s: %d", degree, count)

        return True

    except (psycopg.Error, IOError) as exc:
        logger.error("Unexpected error in main process: %s", exc)
        return False

    finally:
        loader.close_connection()


if __name__ == "__main__":
    SUCCESS = main()
    sys.exit(0 if SUCCESS else 1)
