#!/usr/bin/env python3
"""
Flask Web Application for Grad Café Data Analysis
Displays query results and provides data update functionality
"""

import os
import psycopg
import subprocess
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify

# Import our query analyzer
from query_data import GradCafeQueryAnalyzer

# Default database configuration
DEFAULT_DB_CONFIG = {
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

def create_app(config=None, db_config=None, scraper=None):
    """Application factory function"""
    app = Flask(__name__)
    
    # Apply configuration
    if config:
        app.config.update(config)
    
    # Set up database configuration
    if db_config:
        app.db_config = db_config
    elif os.getenv('DATABASE_URL'):
        # Parse DATABASE_URL for testing
        import urllib.parse
        url = urllib.parse.urlparse(os.getenv('DATABASE_URL'))
        app.db_config = {
            'host': url.hostname,
            'port': url.port or 5432,
            'dbname': url.path[1:],  # Remove leading slash
            'user': url.username,
            'password': url.password or ''
        }
    else:
        app.db_config = DEFAULT_DB_CONFIG.copy()
    
    # Set up scraper (for dependency injection in tests)
    app.scraper = scraper

    def get_db_connection():
        """Get database connection"""
        try:
            conn = psycopg.connect(**app.db_config)
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None

    def run_data_pipeline():
        """Run the complete data pipeline: scrape -> clean -> LLM -> load"""
        global scraping_status
        
        print(f"[DEBUG] Starting data pipeline in thread {threading.current_thread().name}")
        
        try:
            scraping_status['is_running'] = True
            scraping_status['error'] = None
            scraping_status['progress'] = 'Starting data pipeline...'
            
            # Use injected scraper if available (for testing)
            if app.scraper:
                print("[DEBUG] Using injected scraper")
                try:
                    result = app.scraper.scrape()
                    print(f"[DEBUG] Scraper completed: {result}")
                    scraping_status['progress'] = 'Complete! Test data loaded'
                    scraping_status['last_update'] = datetime.now()
                except Exception as e:
                    print(f"[DEBUG] Scraper failed with exception: {e}")
                    raise e  # Re-raise to be caught by outer try/except
                return
            
            # Get the correct working directory (where flask_app.py is located)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"[DEBUG] Base directory: {base_dir}")
            
            # Step 1: Incremental scraping
            scraping_status['progress'] = 'Step 1/4: Scraping new data...'
            print("[DEBUG] Running incremental_scraper.py...")
            
            result = subprocess.run(['python', 'incremental_scraper.py'], 
                                  capture_output=True, text=True, cwd=base_dir)
            
            print(f"[DEBUG] Scraper return code: {result.returncode}")
            print(f"[DEBUG] Scraper stdout: {result.stdout}")
            if result.stderr:
                print(f"[DEBUG] Scraper stderr: {result.stderr}")
            
            if result.returncode != 0:
                raise Exception(f"Scraping failed: {result.stderr}")
            
            # Check if new data was found
            if "No new data found" in result.stdout or "No new data" in result.stdout:
                scraping_status['progress'] = 'No new data available'
                scraping_status['is_running'] = False
                scraping_status['last_update'] = datetime.now()
                print("[DEBUG] No new data found, ending pipeline")
                return
            
            # Step 2: Clean new data
            scraping_status['progress'] = 'Step 2/4: Cleaning new data...'
            print("[DEBUG] Running clean.py...")
            
            result = subprocess.run(['python', 'clean.py', '--input', 'new_applicant_data.json', 
                                   '--output', 'new_cleaned_applicant_data.json'], 
                                  capture_output=True, text=True, cwd=base_dir)
            
            if result.returncode != 0:
                raise Exception(f"Cleaning failed: {result.stderr}")
            
            # Step 3: LLM standardization
            scraping_status['progress'] = 'Step 3/4: LLM standardization...'
            print("[DEBUG] Running LLM standardization...")
            
            llm_dir = os.path.join(base_dir, 'llm_hosting')
            result = subprocess.run(['python', 'app.py', '--file', '../new_cleaned_applicant_data.json', 
                                   '--stdout'], 
                                  capture_output=True, text=True, cwd=llm_dir)
            
            if result.returncode != 0:
                raise Exception(f"LLM processing failed: {result.stderr}")
            
            # Save LLM output
            llm_output_path = os.path.join(base_dir, 'new_llm_extend_applicant_data.jsonl')
            with open(llm_output_path, 'w') as f:
                f.write(result.stdout)
            
            # Step 4: Load new data into database
            scraping_status['progress'] = 'Step 4/4: Loading new data into database...'
            print("[DEBUG] Loading data to database...")
            
            # Load and append new data to database
            new_count = load_new_data_to_database(llm_output_path)
            
            scraping_status['progress'] = f'Complete! Added {new_count} new records'
            scraping_status['last_update'] = datetime.now()
            print(f"[DEBUG] Pipeline complete! Added {new_count} new records")
            
        except Exception as e:
            print(f"[DEBUG] Pipeline error: {str(e)}")
            import traceback
            traceback.print_exc()
            scraping_status['error'] = str(e)
            scraping_status['progress'] = f'Error: {str(e)}'
        
        finally:
            scraping_status['is_running'] = False
            print("[DEBUG] Data pipeline thread finished")

    def load_new_data_to_database(filename: str) -> int:
        """Load new data from JSONL file into database"""
        try:
            # Import the data loader functionality
            from load_data import GradCafeDataLoader
            
            loader = GradCafeDataLoader(app.db_config)
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
    @app.route('/analysis')
    def index():
        """Main analysis page displaying query results"""
        try:
            # Get all query results
            analyzer = GradCafeQueryAnalyzer(app.db_config)
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

    @app.route('/pull-data', methods=['POST'])
    def pull_data():
        """Endpoint to trigger data pulling"""
        global scraping_status
        
        if scraping_status['is_running']:
            return jsonify({'busy': True}), 409
        
        # Start data pipeline in background thread
        thread = threading.Thread(target=run_data_pipeline)
        thread.daemon = True
        thread.start()
        
        return jsonify({'ok': True}), 202

    @app.route('/update-analysis', methods=['POST'])
    def update_analysis():
        """Endpoint to refresh analysis results"""
        global scraping_status
        
        if scraping_status['is_running']:
            return jsonify({'busy': True}), 409
        
        return jsonify({'ok': True}), 200

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
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True)
