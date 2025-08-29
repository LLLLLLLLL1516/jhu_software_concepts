"""
Main routes blueprint for Wei Liu's personal website.
Contains all the route handlers for the website pages.
"""

from flask import Blueprint, render_template

# Create the main blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Homepage route displaying Wei Liu's bio and profile information.
    
    Returns:
        str: Rendered HTML template for the homepage
    """
    return render_template('index.html')


@main_bp.route('/contact')
def contact():
    """
    Contact page route displaying contact information and social links.
    
    Returns:
        str: Rendered HTML template for the contact page
    """
    return render_template('contact.html')


@main_bp.route('/projects')
def projects():
    """
    Projects page route displaying information about Python projects.
    
    Returns:
        str: Rendered HTML template for the projects page
    """
    return render_template('projects.html')
