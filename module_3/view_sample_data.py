#!/usr/bin/env python3
"""
view_sample_data.py - Display sample data from the PostgreSQL database

This script connects to the gradcafe_db database and displays sample records
in a formatted, readable way.

Author: Wei Liu
Date: September 2025
"""

import psycopg
from typing import List, Dict, Any
import sys

# Database configuration (same as load_data.py)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'gradcafe_db',
    'user': 'momo',  # Updated for PostgreSQL.app
    'password': ''   # PostgreSQL.app typically doesn't require a password
}

def connect_to_database():
    """Connect to the PostgreSQL database"""
    try:
        connection = psycopg.connect(**DB_CONFIG)
        print("✅ Successfully connected to PostgreSQL database")
        return connection
    except psycopg.Error as e:
        print(f"❌ Failed to connect to database: {e}")
        print("\n💡 Try updating the DB_CONFIG in this script to match your setup:")
        print("   - If using PostgreSQL.app, try user='momo' and password=''")
        print("   - If using Homebrew PostgreSQL, try user='postgres'")
        return None

def format_value(value, max_length=50):
    """Format a value for display, truncating if too long"""
    if value is None:
        return "NULL"
    
    str_value = str(value)
    if len(str_value) > max_length:
        return str_value[:max_length-3] + "..."
    return str_value

def display_sample_data(connection, limit=10):
    """Display sample data from the applicant_data table"""
    try:
        with connection.cursor() as cursor:
            # First, get the table structure to show all columns
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'applicant_data' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            print(f"\n📋 Database Table Structure:")
            print("=" * 60)
            for col_name, data_type in columns:
                print(f"   {col_name}: {data_type}")
            
            # Get sample records with ALL columns
            cursor.execute("""
                SELECT * FROM applicant_data 
                ORDER BY p_id 
                LIMIT %s
            """, (limit,))
            
            records = cursor.fetchall()
            
            if not records:
                print("❌ No data found in the applicant_data table")
                return
            
            print(f"\n📊 Displaying first {len(records)} records with ALL columns:")
            print("=" * 140)
            
            # Get column names for display
            column_names = [desc[0] for desc in cursor.description]
            
            for i, record in enumerate(records, 1):
                print(f"\n🎓 Record {i}:")
                print("-" * 80)
                
                # Display each column and its value
                for j, (col_name, value) in enumerate(zip(column_names, record)):
                    formatted_value = format_value(value, 80)
                    print(f"   {col_name:25}: {formatted_value}")
                
                if i < len(records):
                    print("=" * 140)
            
    except psycopg.Error as e:
        print(f"❌ Error querying data: {e}")

def display_summary_stats(connection):
    """Display summary statistics about the data"""
    try:
        with connection.cursor() as cursor:
            # Total count
            cursor.execute("SELECT COUNT(*) FROM applicant_data")
            total_count = cursor.fetchone()[0]
            
            # Status distribution (top 5)
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM applicant_data 
                WHERE status IS NOT NULL AND status != ''
                GROUP BY status 
                ORDER BY count DESC 
                LIMIT 5
            """)
            status_dist = cursor.fetchall()
            
            # Degree distribution
            cursor.execute("""
                SELECT degree, COUNT(*) as count
                FROM applicant_data 
                WHERE degree IS NOT NULL AND degree != ''
                GROUP BY degree 
                ORDER BY count DESC 
                LIMIT 5
            """)
            degree_dist = cursor.fetchall()
            
            # GPA statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_with_gpa,
                    ROUND(AVG(gpa)::numeric, 2) as avg_gpa,
                    ROUND(MIN(gpa)::numeric, 2) as min_gpa,
                    ROUND(MAX(gpa)::numeric, 2) as max_gpa
                FROM applicant_data 
                WHERE gpa IS NOT NULL
            """)
            gpa_stats = cursor.fetchone()
            
            print(f"\n📈 Database Summary Statistics:")
            print("=" * 60)
            print(f"📊 Total Records: {total_count:,}")
            
            print(f"\n🎯 Top Admission Statuses:")
            for status, count in status_dist:
                percentage = (count / total_count) * 100
                print(f"   {status}: {count:,} ({percentage:.1f}%)")
            
            print(f"\n🎓 Top Degree Types:")
            for degree, count in degree_dist:
                percentage = (count / total_count) * 100
                print(f"   {degree}: {count:,} ({percentage:.1f}%)")
            
            if gpa_stats and gpa_stats[0] > 0:
                total_with_gpa, avg_gpa, min_gpa, max_gpa = gpa_stats
                print(f"\n📚 GPA Statistics:")
                print(f"   Records with GPA: {total_with_gpa:,}")
                print(f"   Average GPA: {avg_gpa}")
                print(f"   GPA Range: {min_gpa} - {max_gpa}")
            
    except psycopg.Error as e:
        print(f"❌ Error getting summary statistics: {e}")

def display_interesting_samples(connection):
    """Display some interesting sample records"""
    try:
        with connection.cursor() as cursor:
            print(f"\n🌟 Some Interesting Records:")
            print("=" * 80)
            
            # High GPA acceptances
            cursor.execute("""
                SELECT program, status, gpa, gre, degree
                FROM applicant_data 
                WHERE status = 'Accepted' AND gpa >= 3.8 AND gpa IS NOT NULL
                ORDER BY gpa DESC 
                LIMIT 3
            """)
            high_gpa = cursor.fetchall()
            
            if high_gpa:
                print(f"\n🏆 High GPA Acceptances (GPA ≥ 3.8):")
                for program, status, gpa, gre, degree in high_gpa:
                    print(f"   • {format_value(program, 50)} | GPA: {gpa} | GRE: {gre or 'N/A'} | {degree}")
            
            # International vs US students
            cursor.execute("""
                SELECT us_or_international, COUNT(*) as count
                FROM applicant_data 
                WHERE us_or_international IS NOT NULL AND us_or_international != ''
                GROUP BY us_or_international
                ORDER BY count DESC
            """)
            intl_dist = cursor.fetchall()
            
            if intl_dist:
                print(f"\n🌍 Student Distribution:")
                for student_type, count in intl_dist:
                    print(f"   • {student_type}: {count:,}")
            
    except psycopg.Error as e:
        print(f"❌ Error getting interesting samples: {e}")

def main():
    """Main function to display sample data"""
    print("🔍 Grad Café Database Sample Data Viewer")
    print("=" * 50)
    
    # Connect to database
    connection = connect_to_database()
    if not connection:
        return False
    
    try:
        # Display sample records
        display_sample_data(connection, limit=5)
        
        # Display summary statistics
        display_summary_stats(connection)
        
        # Display interesting samples
        display_interesting_samples(connection)
        
        print(f"\n✅ Sample data display completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    finally:
        connection.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
