# Module 3 - Databases Assignment (Flask Web Application with Dynamic Data Management)

**Author:** Wei Liu (wliu125@jh.edu)  
**Course:** EN.605.256.8VL.FA25 - Software Concepts  
**Due Date:** September 14, 2025

## 🎯 Overview

This module builds upon Module 2's data collection and cleaning pipeline by creating a comprehensive Flask web application that displays SQL query results and provides dynamic data management capabilities. The application includes dashboard, real-time data updates, and automated pipeline management.

## 📁 Project Structure

```
module_3/
├── flask_app.py                    # Main Flask web application
├── incremental_scraper.py          # Smart incremental data collection
├── load_data.py                    # PostgreSQL database integration
├── query_data.py                   # SQL analysis and reporting
├── clean.py                        # Enhanced data cleaning
├── requirements.txt                # Python dependencies
├── templates/                      # HTML templates
│   ├── base.html                   # Base template with Bootstrap
│   ├── index.html                  # Main dashboard
│   └── error.html                  # Error handling
├── static/                         # Static assets
│   ├── css/style.css              # Custom styling
│   └── js/main.js                 # JavaScript utilities
├── llm_hosting/                    # LLM standardization service
└── module_3_query_analysis_report.pdf  # Generated analysis report
```

## 🏗️ Technical Architecture

### Database Schema
- **Database:** PostgreSQL (`gradcafe_db`)
- **Table:** `applicant_data` with 15 columns
- **Primary Key:** `p_id` (auto-increment)
- **Records:** 50,000+ grad school admission entries

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| p_id | integer | Unique identifier (auto-generated) |
| program | text | University and Department |
| comments | text | Comments |
| date_added | date | Date Added |
| url | text | Link to Post on Grad Café |
| status | text | Admission Status |
| term | text | Start Term |
| us_or_international | text | Student nationality |
| gpa | float | Student GPA |
| gre | float | Student GRE Quantitative |
| gre_v | float | Student GRE Verbal |
| gre_aw | float | Student GRE Analytical Writing |
| degree | text | Student Program Degree Type |
| llm_generated_program | text | LLM Generated Department/Program |
| llm_generated_university | text | LLM Generated University |

### Flask Application Structure
- **Main routes:** `/`, `/pull_data`, `/update_analysis`, `/status`
- **Template inheritance:** `base.html` with Bootstrap 5
- **Static assets:** CSS, JavaScript, and images
- **Error handling:** Custom error pages and comprehensive logging

## 🔧 Core Components

### 1. Database Setup (`load_data.py`)
- **PostgreSQL Integration:** Using psycopg3 for modern connectivity
- **Schema Management:** Automatic table creation with proper data types
- **Batch Processing:** Efficient loading of 50,000+ records
- **Data Validation:** Robust error handling and data transformation
- **Progress Tracking:** Real-time loading progress with statistics
- **Command-line Support:** Flexible input file specification

#### Data Mapping
| JSONL Field | Database Column | Transformation |
|-------------|-----------------|----------------|
| program | program | Direct mapping |
| comments | comments | Direct mapping |
| date_added | date_added | Parsed to DATE format |
| url | url | Direct mapping |
| status | status | Direct mapping |
| semester | term | Field name change |
| applicant_type | us_or_international | Field name change |
| gpa | gpa | Converted to float |
| gre_total | gre | Converted to float |
| gre_verbal | gre_v | Converted to float |
| gre_aw | gre_aw | Converted to float |
| degree | degree | Direct mapping |
| llm-generated-program | llm_generated_program | Field name normalization |
| llm-generated-university | llm_generated_university | Field name normalization |

### 2. SQL Query Analysis (`query_data.py`)
- **GradCafeQueryAnalyzer Class:** Object-oriented query management
- **10 Analytical Queries:** Comprehensive data analysis covering:
  - Fall 2025 application counts
  - International student percentages
  - Average GPA/GRE metrics
  - Acceptance rates by demographics
  - University-specific statistics

### 3. Flask Web Application (`flask_app.py`)
- **Dashboard:** Bootstrap-based responsive interface
- **Real-time Statistics:** Database metrics and status updates
- **Interactive Features:**
  - **"Pull Data" Button:** Complete 4-step pipeline automation
  - **"Update Analysis" Button:** Instant results refresh
- **Background Processing:** Threading for non-blocking operations
- **AJAX Status Polling:** Real-time progress updates
- **Comprehensive Error Handling:** User-friendly error messages

#### Dashboard Components
- **Header Section:** Title and action buttons
- **Database Stats:** Total records, latest entry, last update
- **Button Explanations:** Clear user guidance
- **Query Results Grid:** Professional card-based layout with:
  - **Card Layout:** Each query result in its own styled card
  - **Visual Hierarchy:** Clear question numbering and descriptions
  - **Result Formatting:** Numbers formatted with commas, percentages clearly marked
  - **SQL Transparency:** Expandable sections showing actual SQL queries
  - **Special Handling:** Tuple results for multi-value data (GPA, GRE scores)
- **Status Indicators:** Real-time progress and error display

#### Professional Styling
- **Modern Design:** Clean, professional appearance
- **Color Scheme:** Primary blue with success/info accents
- **Animations:** Smooth transitions and hover effects
- **Responsive Layout:** Works on desktop, tablet, and mobile
- **Typography:** Clear, readable fonts with proper hierarchy

### 4. Incremental Data Collection (`incremental_scraper.py`)
- **Smart Scraping:** Only collects NEW data based on database timestamps
- **Efficiency Optimization:** Dramatically reduces processing time
- **Duplicate Prevention:** Automatic filtering of existing entries
- **Seamless Integration:** Works with existing cleaning and LLM pipeline
- **Date-based Filtering:** Intelligent determination of data freshness

### 5. Professional UI/UX (`templates/` and `static/`)
- **Bootstrap 5 Framework:** Modern, responsive design
- **Custom CSS:** Professional styling with animations
- **Mobile-friendly Layout:** Responsive across all devices
- **Interactive Elements:** Hover effects and smooth transitions
- **Clear User Guidance:** Explanatory text and intuitive interface

## 📊 Query Results Summary

| Question | Result |
|----------|--------|
| 1. Fall 2025 entries | **6,631** |
| 2. International student percentage | **53.53%** |
| 3. Average metrics | **GPA: 3.77, GRE: 161.87, GRE V: 165.44, GRE AW: 5.50** |
| 4. American Fall 2025 GPA | **3.77** |
| 5. Fall 2025 acceptance rate | **35.88%** |
| 6. Fall 2025 accepted GPA | **3.76** |
| 7. JHU CS Masters entries | **35** |
| 8. Georgetown CS PhD 2025 acceptances | **6** |
| 9. Penn State international % Fall 2025 | **58.33%** |
| 10. Penn State 2025 acceptances | **25** |

## 🚀 Usage Instructions

### Initial Setup

#### 1. Install Dependencies
```bash
cd module_3
pip install -r requirements.txt
```

#### 2. Set Up PostgreSQL Database
```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database
createdb gradcafe_db

# Or using psql
psql -U postgres
CREATE DATABASE gradcafe_db;
\q
```

#### 3. Configure Database Connection
Edit the `DB_CONFIG` section in `load_data.py` if needed:
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'gradcafe_db',
    'user': 'momo',  # Your PostgreSQL username
    'password': ''   # Your PostgreSQL password
}
```

#### 4. Load Initial Data
```bash
python load_data.py
```

#### 5. Generate Analysis Report
```bash
python query_data.py
```

### Flask Web Application

#### Start the Application
```bash
python flask_app.py
```

#### Access the Dashboard
1. Open browser to: `http://localhost:8080`
2. View analysis dashboard with all 10 query results
3. Use **"Pull Data"** button to scrape and add new entries
4. Use **"Update Analysis"** button to refresh results

### Manual Pipeline (Alternative)

If you need to run the pipeline manually:

```bash
# 1. Scrape new data
python incremental_scraper.py

# 2. Clean new data
python clean.py --input new_applicant_data.json --output new_cleaned_applicant_data.json

# 3. LLM processing
cd llm_hosting
python app.py --file ../new_cleaned_applicant_data.json --stdout > ../new_llm_extend_applicant_data.jsonl
cd ..

# 4. Load to database
python load_data.py --input new_llm_extend_applicant_data.jsonl
```

## 🚀 Future Enhancements

- **Query Result Caching:** Faster page loads for repeated queries
- **User Authentication:** Session management and user accounts
- **Data Visualization:** Interactive charts and graphs
- **Export Functionality:** CSV/Excel export of analysis results
- **Advanced Filtering:** Search and filter capabilities
- **API Endpoints:** RESTful API for external integrations

## 📝 Known Issues

- **Initial Load Time:** May take a few seconds due to query execution on 50,000+ records
- **"Last Update" Display:** Shows "Never" until first use of "Pull Data" button
- **LLM Warnings:** Deprecation warnings during processing (functionality unaffected)
