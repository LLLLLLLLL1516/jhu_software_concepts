Architecture Overview
=====================

This document describes the architecture of the GradCafe Data Analysis system, including the web, ETL, and database layers and their responsibilities.

System Architecture
-------------------

The GradCafe Data Analysis system follows a layered architecture pattern with clear separation of concerns:

.. code-block:: text

    ┌─────────────────────────────────────────────────┐
    │           Web Interface Layer                   │
    │         (Flask Application)                     │
    └─────────────────────────────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────────────┐
    │           Business Logic Layer                  │
    │    (Query Analysis & Data Processing)           │
    └─────────────────────────────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────────────┐
    │              ETL Pipeline Layer                 │
    │    (Extract, Transform, Load)                   │
    └─────────────────────────────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────────────┐
    │            Data Storage Layer                   │
    │         (PostgreSQL Database)                   │
    └─────────────────────────────────────────────────┘

Layer Responsibilities
----------------------

Web Layer
~~~~~~~~~

**Component**: ``flask_app.py``

**Responsibilities**:

* Serve the web interface for users to interact with the system
* Provide RESTful API endpoints for data operations
* Handle HTTP requests and responses
* Manage session state and busy indicators
* Render HTML templates with analysis results
* Coordinate background operations (pull data, update analysis)

**Key Features**:

* Dependency injection for testability
* Thread-safe operation management
* Real-time status updates
* Error handling and user feedback

ETL Layer
~~~~~~~~~

The ETL (Extract, Transform, Load) layer consists of multiple components working together:

**Extract Component**: ``scrape.py`` and ``incremental_scraper.py``

**Responsibilities**:

* Fetch admission data from GradCafe website
* Respect robots.txt and implement polite scraping
* Handle pagination and data extraction
* Manage incremental updates (only new data)
* Save raw data to JSON format

**Transform Component**: ``clean.py``

**Responsibilities**:

* Parse and validate raw admission data
* Standardize data formats (dates, GPA, GRE scores)
* Handle missing or malformed data
* Apply data quality rules
* Generate cleaned data output

**Load Component**: ``load_data.py``

**Responsibilities**:

* Connect to PostgreSQL database
* Create and manage database schema
* Insert cleaned data into tables
* Handle duplicate detection
* Manage transaction integrity
* Log operations for audit trail

Database Layer
~~~~~~~~~~~~~~

**Component**: PostgreSQL Database

**Responsibilities**:

* Store admission data persistently
* Provide ACID compliance for data integrity
* Support complex SQL queries for analysis
* Maintain indexes for query performance
* Handle concurrent access

**Schema Design**:

The database uses a single denormalized table ``admission_results`` with columns for:

* Application details (university, program, degree)
* Applicant information (GPA, GRE scores)
* Decision information (status, date, season)
* Metadata (submission date, comments)

Query & Analysis Layer
~~~~~~~~~~~~~~~~~~~~~~

**Component**: ``query_data.py``

**Responsibilities**:

* Execute predefined analytical queries
* Calculate admission statistics
* Generate summary reports
* Format results for presentation
* Support custom query execution

**Analysis Types**:

* Acceptance rates by program
* GPA/GRE score distributions
* Seasonal admission trends
* University-specific statistics
* Decision timeline analysis

Data Flow
---------

1. **Data Collection Flow**:

   .. code-block:: text

      GradCafe Website → Scraper → Raw JSON → Cleaner → Cleaned JSON → Loader → PostgreSQL

2. **Analysis Flow**:

   .. code-block:: text

      PostgreSQL → Query Analyzer → Statistics → Flask App → Web Interface → User

3. **Incremental Update Flow**:

   .. code-block:: text

      Database (last date) → Incremental Scraper → New Data Only → ETL Pipeline → Database

Design Patterns
---------------

Dependency Injection
~~~~~~~~~~~~~~~~~~~~

The system uses dependency injection to improve testability:

.. code-block:: python

   def create_app(scraper=None, db_config=None):
       """Create Flask app with optional dependencies."""
       if scraper is None:
           scraper = GradCafeListScraper()
       if db_config is None:
           db_config = DEFAULT_DB_CONFIG
       # ... rest of app creation

This allows tests to inject mock objects without hitting real services.

Singleton Pattern
~~~~~~~~~~~~~~~~~

The Flask application uses a singleton pattern for managing operation state:

.. code-block:: python

   is_running = False  # Global state for operation status
   
   def check_busy():
       """Check if an operation is running."""
       global is_running
       return is_running

Factory Pattern
~~~~~~~~~~~~~~~

The application uses factory pattern for creating configured instances:

.. code-block:: python

   def create_app(config=None):
       """Application factory."""
       app = Flask(__name__)
       if config:
           app.config.update(config)
       return app

Error Handling Strategy
------------------------

The system implements comprehensive error handling:

1. **Network Errors**: Retry logic with exponential backoff
2. **Database Errors**: Transaction rollback and logging
3. **Data Validation Errors**: Skip invalid records with logging
4. **User Input Errors**: Validation and feedback messages
5. **System Errors**: Graceful degradation and error pages

Performance Considerations
--------------------------

* **Caching**: Results cached in memory during sessions
* **Pagination**: Large result sets paginated for performance
* **Indexing**: Database indexes on frequently queried columns
* **Connection Pooling**: Reuse database connections
* **Async Operations**: Background threads for long-running tasks

Security Considerations
-----------------------

* **SQL Injection Prevention**: Parameterized queries
* **Input Validation**: Sanitize all user inputs
* **Rate Limiting**: Prevent abuse of scraping endpoints
* **Error Messages**: Avoid exposing sensitive information
* **Database Credentials**: Environment variables for secrets

Scalability
-----------

The architecture supports horizontal scaling:

* **Stateless Web Layer**: Can run multiple Flask instances
* **Database Scaling**: PostgreSQL supports read replicas
* **ETL Parallelization**: Can run multiple scrapers
* **Load Balancing**: Nginx or similar for distribution

Future Enhancements
-------------------

Potential architectural improvements:

* **Message Queue**: Add Redis/RabbitMQ for job processing
* **Caching Layer**: Add Redis for result caching
* **API Gateway**: Centralized API management
* **Microservices**: Split into smaller services
* **Container Orchestration**: Kubernetes deployment
* **Monitoring**: Add Prometheus/Grafana stack
