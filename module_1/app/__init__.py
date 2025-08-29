"""
Flask application factory for Wei Liu's personal website.
This module creates and configures the Flask application instance.
"""

from flask import Flask


def create_app():
    """
    Application factory function that creates and configures the Flask app.
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Create Flask application instance
    app = Flask(__name__)
    
    # Configure the application
    # This is not needed for this assignment, but it's a Flask development best practice to always set a SECRET_KEY
    # If needed later, replace this to load from environment variables
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    # Register blueprints
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    return app
