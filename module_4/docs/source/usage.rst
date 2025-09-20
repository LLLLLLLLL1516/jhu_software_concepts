Usage Guide
===========

This guide explains how to use the GradCafe Data Analysis system.

Quick Start
-----------

1. **Scrape Data from GradCafe**

   .. code-block:: bash

      python src/scrape.py

   This will collect admission data from GradCafe and save it to ``applicant_data.json``.

2. **Clean the Data**

   .. code-block:: bash

      python src/clean.py

   This processes raw data and creates ``cleaned_applicant_data.json``.

3. **Load Data into Database**

   .. code-block:: bash

      python src/load_data.py

   This loads cleaned data into PostgreSQL database.

4. **Run Analytics Queries**

   .. code-block:: bash

      python src/query_data.py

   This executes predefined SQL queries for admission insights.

5. **Start Web Application**

   .. code-block:: bash

      python src/flask_app.py

   Access the application at ``http://localhost:8080``.

Detailed Usage
--------------

Web Scraping
~~~~~~~~~~~~

The scraper respects robots.txt and implements polite scraping:

.. code-block:: python

   from scrape import GradCafeListScraper
   
   scraper = GradCafeListScraper(email="your_email@example.com")
   results = scraper.scrape_all_pages(max_pages=100)
   scraper.save_to_json(results, "output.json")

Data Cleaning
~~~~~~~~~~~~~

Clean and standardize admission data:

.. code-block:: python

   from clean import GradCafeDataCleaner
   
   cleaner = GradCafeDataCleaner("raw_data.json")
   cleaner.load_data()
   cleaner.clean_all_data()
   cleaner.save_cleaned_data("cleaned_data.json")

Database Operations
~~~~~~~~~~~~~~~~~~~

Load data into PostgreSQL:

.. code-block:: python

   from load_data import GradCafeDataLoader
   
   loader = GradCafeDataLoader(db_config)
   loader.connect_to_database()
   loader.create_table()
   loader.load_json_data("cleaned_data.json")
   loader.insert_data()

Query Analysis
~~~~~~~~~~~~~~

Run analytical queries:

.. code-block:: python

   from query_data import GradCafeQueryAnalyzer
   
   analyzer = GradCafeQueryAnalyzer(db_config)
   analyzer.connect_to_database()
   analyzer.run_all_queries()
   analyzer.print_summary_report()

Incremental Updates
~~~~~~~~~~~~~~~~~~~

Scrape only new data:

.. code-block:: python

   from incremental_scraper import IncrementalGradCafeScraper
   
   scraper = IncrementalGradCafeScraper(db_config=db_config)
   new_data = scraper.scrape_new_data_only(max_pages=50)
   scraper.save_new_data(new_data, "new_data.json")

Flask Web Application
~~~~~~~~~~~~~~~~~~~~~

The Flask app provides a web interface with REST API endpoints:

**Available Endpoints:**

* ``GET /`` - Main analysis page
* ``GET /analysis`` - Alias for main page
* ``POST /pull-data`` - Trigger data pull
* ``POST /update-analysis`` - Update analysis
* ``GET /status`` - Check operation status

**Using the Web Interface:**

1. Navigate to ``http://localhost:8080``
2. Click "Pull Data" to fetch latest data
3. Click "Update Analysis" to refresh analytics
4. View results in the dashboard

Command Line Interface
----------------------

All modules can be run from command line:

.. code-block:: bash

   # Full data pipeline
   python src/scrape.py && \
   python src/clean.py && \
   python src/load_data.py && \
   python src/query_data.py

   # Incremental update
   python src/incremental_scraper.py

   # Start web server
   python src/flask_app.py

Configuration
-------------

Database Configuration
~~~~~~~~~~~~~~~~~~~~~~

Edit database settings in each module:

.. code-block:: python

   DB_CONFIG = {
       'host': 'localhost',
       'port': 5432,
       'dbname': 'gradcafe_db',
       'user': 'your_user',
       'password': 'your_password'
   }

Scraping Configuration
~~~~~~~~~~~~~~~~~~~~~~

Adjust scraping parameters:

.. code-block:: python

   # Maximum pages to scrape
   MAX_PAGES = 100
   
   # Rate limiting (seconds between requests)
   DELAY = 1.0
   
   # User agent email
   EMAIL = "your_email@example.com"

Best Practices
--------------

1. **Rate Limiting**: Always respect rate limits when scraping
2. **Database Backups**: Regularly backup your PostgreSQL database
3. **Error Handling**: Check logs for any errors during processing
4. **Testing**: Run tests after configuration changes
5. **Documentation**: Keep documentation updated with changes
