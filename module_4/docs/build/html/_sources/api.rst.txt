API Reference
=============

This section provides detailed API documentation for the Flask web application endpoints.

REST API Endpoints
------------------

Main Routes
~~~~~~~~~~~

.. http:get:: /

   Display the main analysis dashboard page.

   **Example request**:

   .. code-block:: bash

      curl http://localhost:8080/

   **Status codes**:
   
   * **200 OK** - Page rendered successfully
   * **500 Internal Server Error** - Server error

.. http:get:: /analysis

   Alias for the main dashboard page.

   **Example request**:

   .. code-block:: bash

      curl http://localhost:8080/analysis

   **Status codes**:
   
   * **200 OK** - Page rendered successfully
   * **500 Internal Server Error** - Server error

Data Operations
~~~~~~~~~~~~~~~

.. http:post:: /pull-data

   Trigger a data pull operation to fetch latest admission data.

   **Example request**:

   .. code-block:: bash

      curl -X POST http://localhost:8080/pull-data

   **Example response** (success):

   .. code-block:: json

      {
          "ok": true
      }

   **Example response** (busy):

   .. code-block:: json

      {
          "busy": true
      }

   **Status codes**:
   
   * **202 Accepted** - Operation started successfully
   * **409 Conflict** - Another operation is in progress

.. http:post:: /update-analysis

   Update the analysis with latest data from the database.

   **Example request**:

   .. code-block:: bash

      curl -X POST http://localhost:8080/update-analysis

   **Example response** (success):

   .. code-block:: json

      {
          "ok": true
      }

   **Example response** (busy):

   .. code-block:: json

      {
          "busy": true
      }

   **Status codes**:
   
   * **200 OK** - Analysis updated successfully
   * **409 Conflict** - Another operation is in progress

Status Monitoring
~~~~~~~~~~~~~~~~~

.. http:get:: /status

   Get the current status of background operations.

   **Example request**:

   .. code-block:: bash

      curl http://localhost:8080/status

   **Example response**:

   .. code-block:: json

      {
          "is_running": false,
          "progress": "",
          "last_update": "2025-09-20 15:30:00",
          "error": null
      }

   **Response fields**:
   
   * **is_running** (*boolean*) - Whether an operation is currently running
   * **progress** (*string*) - Current progress message
   * **last_update** (*string*) - Timestamp of last successful update
   * **error** (*string|null*) - Error message if operation failed

   **Status codes**:
   
   * **200 OK** - Status retrieved successfully

Python API
----------

Flask Application Factory
~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: create_app(scraper=None, db_config=None)

   Create and configure the Flask application.

   :param scraper: Optional scraper instance for dependency injection
   :type scraper: GradCafeListScraper or None
   :param db_config: Optional database configuration
   :type db_config: dict or None
   :return: Configured Flask application
   :rtype: Flask

   **Example**:

   .. code-block:: python

      from flask_app import create_app
      
      # Default configuration
      app = create_app()
      
      # With custom scraper
      from scrape import GradCafeListScraper
      custom_scraper = GradCafeListScraper(email="test@example.com")
      app = create_app(scraper=custom_scraper)
      
      # With custom database
      custom_db = {'host': 'localhost', 'dbname': 'test_db'}
      app = create_app(db_config=custom_db)

Error Handling
--------------

The API implements standard HTTP error codes:

* **200 OK** - Request successful
* **202 Accepted** - Asynchronous operation started
* **404 Not Found** - Resource not found
* **409 Conflict** - Resource conflict (busy state)
* **500 Internal Server Error** - Server error

Error Response Format
~~~~~~~~~~~~~~~~~~~~~

Error responses follow this format:

.. code-block:: json

   {
       "error": "Error message description",
       "status": 500
   }

Rate Limiting
-------------

The API implements rate limiting for data operations:

* Only one pull-data or update-analysis operation can run at a time
* Concurrent requests receive a 409 Conflict response
* Check ``/status`` endpoint to monitor operation progress

Authentication
--------------

Currently, the API does not require authentication. In production environments, consider implementing:

* API key authentication
* OAuth 2.0
* JWT tokens
* Session-based authentication

WebSocket Support
-----------------

For real-time updates, consider implementing WebSocket connections:

.. code-block:: javascript

   const socket = new WebSocket('ws://localhost:8080/ws');
   
   socket.onmessage = function(event) {
       const data = JSON.parse(event.data);
       console.log('Progress:', data.progress);
   };

Testing the API
---------------

Use pytest to test API endpoints:

.. code-block:: bash

   pytest tests/test_buttons.py -v
   pytest tests/test_flask_page.py -v

Or use curl for manual testing:

.. code-block:: bash

   # Test pull data
   curl -X POST http://localhost:8080/pull-data
   
   # Check status
   curl http://localhost:8080/status
   
   # Update analysis
   curl -X POST http://localhost:8080/update-analysis
