#!/usr/bin/env python3
"""
view_rich_data.py - Display records with comments and GRE scores

This script shows records where both comments and GRE scores are present
to demonstrate the richer data entries in the database.
"""

import psycopg
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'gradcafe_db',
    'user': 'momo',
    'password': ''
}

def format_value(value, max_length=80):
    """Format a value for display, truncating if too long"""
    if value is None:
        return "NULL"
    
    str_value = str(value)
    if len(str_value) > max_length:
        return str_value[:max_length-3] + "..."
    return str_value

def main():
    """Display records with comments and GRE scores exactly as in database"""
    print("🔍 Grad Café Records with Comments and GRE Scores")
    print("=" * 60)
    
    try:
        connection = psycopg.connect(**DB_CONFIG)
        print("✅ Connected to database")
        
        with connection.cursor() as cursor:
            # Get ALL columns in database order
            cursor.execute("""
                SELECT * FROM applicant_data 
                WHERE comments IS NOT NULL 
                  AND comments != '' 
                  AND gre IS NOT NULL
                ORDER BY p_id
                LIMIT 5
            """)
            
            records = cursor.fetchall()
            
            if not records:
                print("❌ No records found with both comments and GRE scores")
                return False
            
            # Get column names from cursor description
            column_names = [desc[0] for desc in cursor.description]
            
            print(f"\n📊 Database columns: {', '.join(column_names)}")
            print(f"✅ Found {len(records)} records with both comments and GRE scores")
            print("=" * 140)
            
            for i, record in enumerate(records, 1):
                print(f"\n🎓 Record {i}:")
                print("-" * 80)
                
                # Display each column exactly as it appears in database
                for col_name, value in zip(column_names, record):
                    formatted_value = format_value(value, 80)
                    print(f"   {col_name:25}: {formatted_value}")
                
                if i < len(records):
                    print("=" * 140)
        
        connection.close()
        print(f"\n✅ Query completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
