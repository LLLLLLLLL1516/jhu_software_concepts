.. GradCafe Data Analysis documentation master file, created by
   sphinx-quickstart on Fri Sep 20 15:57:39 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to GradCafe Data Analysis's documentation!
===================================================

This project provides comprehensive tools for scraping, cleaning, analyzing, and visualizing 
graduate school admission data from GradCafe. It includes a Flask web application, data 
processing pipelines, and SQL query analysis tools.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
   installation
   usage
   architecture
   api
   testing

Project Overview
----------------

The GradCafe Data Analysis system consists of several key components:

* **Web Scraping**: Automated data collection from GradCafe
* **Data Cleaning**: Processing and standardization of admission data
* **Database Management**: PostgreSQL integration for data storage
* **Query Analysis**: SQL-based analytics for admission insights
* **Web Interface**: Flask application for data visualization
* **Incremental Updates**: Smart scraping for new data only

Key Features
------------

* Comprehensive test coverage (100% for core modules)
* Dependency injection for testability
* RESTful API endpoints
* Real-time data updates
* Automated data pipeline
* Extensive documentation

Modules
-------

The project is organized into the following main modules:

* :mod:`scrape` - Web scraping functionality
* :mod:`clean` - Data cleaning and processing
* :mod:`load_data` - Database loading operations
* :mod:`query_data` - SQL analytics queries
* :mod:`flask_app` - Web application interface
* :mod:`incremental_scraper` - Incremental data updates

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
