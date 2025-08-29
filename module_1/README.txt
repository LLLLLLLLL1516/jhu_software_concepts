Wei Liu's Personal Website - Module 1 Project
==============================================

This is a Flask-based personal website showcasing Wei Liu's professional background, 
contact information, and projects.

REQUIREMENTS
------------
- Python 3.10 or higher
- pip (Python package installer)

INSTALLATION & SETUP
-------------------
1. Navigate to the module_1 directory:
   cd module_1

2. Create a virtual environment (recommended):
   python -m venv venv

3. Activate the virtual environment:
   - On Windows: venv\Scripts\activate
   - On macOS/Linux: source venv/bin/activate

4. Install required dependencies:
   pip install -r requirements.txt

RUNNING THE APPLICATION
----------------------
1. Make sure you're in the module_1 directory
2. Run the application:
   python run.py

3. Open your web browser and navigate to:
   http://localhost:8080
   or
   http://0.0.0.0:8080

The application will start on port 8080 as required.

WEBSITE STRUCTURE
----------------
The website contains three main pages:

1. Homepage (/) - Features Wei Liu's biography and professional background
   - Name and current position
   - Professional bio with educational background
   - Profile image

2. Contact Page (/contact) - Contact information and professional links
   - Email address
   - LinkedIn profile
   - Professional background summary

3. Projects Page (/projects) - Information about projects
   - Module 1 project details and description
   - Technologies used and key features
   - GitHub repository link

FEATURES
--------
- Responsive web design that works on desktop and mobile
- Navigation bar positioned in the top-right corner
- Active tab highlighting in navigation
- Professional color scheme and modern styling
- Flask blueprints for organized code structure
- HTML templates with Jinja2 templating
- Custom CSS styling for professional appearance

TECHNICAL DETAILS
----------------
- Built with Flask web framework
- Uses Flask blueprints for modular organization
- HTML5 and CSS3 for modern web standards
- Responsive design with CSS Grid and Flexbox
- Professional color palette and typography
- Clean, maintainable code structure

PROJECT STRUCTURE
-----------------
module_1/
├── run.py                 # Main application runner
├── app/
│   ├── __init__.py       # Flask app factory
│   ├── routes/
│   │   ├── __init__.py
│   │   └── main.py       # Route handlers
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css # Custom styling
│   │   └── images/
│   │       └── placeholder.jpg # Profile image
│   └── templates/
│       ├── base.html     # Base template
│       ├── index.html    # Homepage
│       ├── contact.html  # Contact page
│       └── projects.html # Projects page
├── requirements.txt      # Python dependencies
└── README.txt           # This file

TROUBLESHOOTING
--------------
- If you get a "Port already in use" error, make sure no other application is running on port 8080
- If you encounter import errors, ensure all dependencies are installed: pip install -r requirements.txt
- Make sure you're using Python 3.10 or higher: python --version
- If the website doesn't load properly, check that you're accessing http://localhost:8080

DEVELOPMENT NOTES
----------------
- The application runs in debug mode for development
- Static files (CSS, images) are served from the app/static directory
- Templates use Jinja2 templating engine for dynamic content
- The navigation bar automatically highlights the current page
- All styling is contained in the single CSS file for easy maintenance

For questions or issues, contact: wliu125@jhu.edu
