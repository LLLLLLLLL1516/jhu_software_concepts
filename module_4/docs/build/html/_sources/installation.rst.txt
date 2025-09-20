Installation Guide
==================

This guide will help you set up the GradCafe Data Analysis project on your system.

Prerequisites
-------------

* Python 3.8 or higher
* PostgreSQL database server
* pip package manager

System Requirements
-------------------

* Operating System: macOS, Linux, or Windows
* Memory: At least 4GB RAM recommended
* Storage: At least 1GB free space for data

Installation Steps
------------------

1. Clone the Repository
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/yourusername/gradcafe-analysis.git
   cd gradcafe-analysis/module_4

2. Create Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -r src/requirements.txt

4. Set Up PostgreSQL Database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a database named ``gradcafe_db``:

.. code-block:: sql

   CREATE DATABASE gradcafe_db;
   CREATE USER your_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE gradcafe_db TO your_user;

5. Configure Database Connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Update the database configuration in your Python files:

.. code-block:: python

   DB_CONFIG = {
       'host': 'localhost',
       'port': 5432,
       'dbname': 'gradcafe_db',
       'user': 'your_user',
       'password': 'your_password'
   }

6. Initialize Database Schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the data loader to create tables:

.. code-block:: bash

   python src/load_data.py

Testing Installation
--------------------

Verify your installation by running the test suite:

.. code-block:: bash

   pytest tests/ -v

All tests should pass if the installation is successful.

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Database Connection Error**
   - Ensure PostgreSQL is running
   - Check database credentials
   - Verify network connectivity

**Import Errors**
   - Ensure all dependencies are installed
   - Check Python path configuration
   - Verify virtual environment is activated

**Permission Errors**
   - Check file permissions
   - Ensure write access to data directories
