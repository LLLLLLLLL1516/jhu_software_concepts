#!/usr/bin/env python3
"""
Flask Web Application for Grad Café Data Analysis
Displays query results and provides data update functionality
"""

import psycopg
import subprocess
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify

# Import our query analyzer
from query_data import GradCafeQueryAnalyzer

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'gradcafe_db',
    'user': 'momo',
    'password': ''
}

# Global variables for tracking operations
scraping_status = {
    'is_running': False,
    'progress': '',
    'last_update': None,
    'error': None
}

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def run_data_pipeline():
    """Run the complete data pipeline: scrape -> clean -> LLM -> load"""
    global scraping_status
    
    try:
        scraping_status['is_running'] = True
        scraping_status['error'] = None
        scraping_status['progress'] = 'Starting data pipeline...'
        
        # Step 1: Incremental scraping
        scraping_status['progress'] = 'Step 1/4: Scraping new data...'
        result = subprocess.run(['python', 'incremental_scraper.py'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode != 0:
            raise Exception(f"Scraping failed: {result.stderr}")
        
        # Check if new data was found
        if "No new data found" in result.stdout:
            scraping_status['progress'] = 'No new data available'
            scraping_status['is_running'] = False
            return
        
        # Step 2: Clean new data
        scraping_status['progress'] = 'Step 2/4: Cleaning new data...'
        result = subprocess.run(['python', 'clean.py', '--input', 'new_applicant_data.json', 
                               '--output', 'new_cleaned_applicant_data.json'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode != 0:
            raise Exception(f"Cleaning failed: {result.stderr}")
        
        # Step 3: LLM standardization
        scraping_status['progress'] = 'Step 3/4: LLM standardization...'
        result = subprocess.run(['python', 'app.py', '--file', '../new_cleaned_applicant_data.json', 
                               '--stdout'], 
                              capture_output=True, text=True, cwd='llm_hosting')
        
        if result.returncode != 0:
            raise Exception(f"LLM processing failed: {result.stderr}")
        
        # Save LLM output
        with open('new_llm_extend_applicant_data.jsonl', 'w') as f:
            f.write(result.stdout)
        
        # Step 4: Load new data into database
        scraping_status['progress'] = 'Step 4/4: Loading new data into database...'
        
        # Load and append new data to database
        new_count = load_new_data_to_database('new_llm_extend_applicant_data.jsonl')
        
        scraping_status['progress'] = f'Complete! Added {new_count} new records'
        scraping_status['last_update'] = datetime.now()
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['progress'] = f'Error: {str(e)}'
    
    finally:
        scraping_status['is_running'] = False

def load_new_data_to_database(filename: str) -> int:
    """Load new data from JSONL file into database"""
    try:
        # Import the data loader functionality
        from load_data import GradCafeDataLoader
        
        loader = GradCafeDataLoader(DB_CONFIG)
        if not loader.connect_to_database():
            raise Exception("Failed to connect to database")
        
        # Count existing records
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM applicant_data")
            initial_count = cursor.fetchone()[0]
        conn.close()
        
        # Load new data
        success = loader.load_data_from_jsonl(filename)
        if not success:
            raise Exception("Failed to load new data")
        
        # Count final records
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM applicant_data")
            final_count = cursor.fetchone()[0]
        conn.close()
        
        loader.close_connection()
        
        return final_count - initial_count
        
    except Exception as e:
        raise Exception(f"Database loading error: {e}")

@app.route('/')
def index():
    """Main analysis page displaying query results"""
    try:
        # Get all query results
        analyzer = GradCafeQueryAnalyzer(DB_CONFIG)
        if not analyzer.connect_to_database():
            return render_template('error.html', error="Failed to connect to database")
        
        # Run all queries
        analyzer.run_all_queries()
        results = analyzer.results
        analyzer.close_connection()
        
        # Get database stats
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM applicant_data")
                total_records = cursor.fetchone()[0]
                
                cursor.execute("SELECT MAX(date_added) FROM applicant_data")
                latest_date = cursor.fetchone()[0]
            conn.close()
        else:
            total_records = 0
            latest_date = None
        
        return render_template('index.html', 
                             results=results, 
                             total_records=total_records,
                             latest_date=latest_date,
                             scraping_status=scraping_status)
        
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/pull_data', methods=['POST'])
def pull_data():
    """Endpoint to trigger data pulling"""
    global scraping_status
    
    if scraping_status['is_running']:
        return jsonify({
            'success': False, 
            'message': 'Data pulling is already in progress'
        })
    
    # Start data pipeline in background thread
    thread = threading.Thread(target=run_data_pipeline)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True, 
        'message': 'Data pulling started'
    })

@app.route('/update_analysis', methods=['POST'])
def update_analysis():
    """Endpoint to refresh analysis results"""
    global scraping_status
    
    if scraping_status['is_running']:
        return jsonify({
            'success': False, 
            'message': 'Cannot update analysis while data pulling is in progress'
        })
    
    # Simply redirect to main page to refresh results
    return jsonify({
        'success': True, 
        'message': 'Analysis updated'
    })

@app.route('/status')
def get_status():
    """Get current scraping status"""
    return jsonify(scraping_status)

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
