#!/usr/bin/env python3
"""
Main application runner for Wei Liu's personal website.
This file starts the Flask development server on port 8080.
"""

from app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    # Run the application on port 8080 as required
    app.run(host='0.0.0.0', port=8080, debug=True)
