# Fund Load Restrictions Information

## Summary
A Django-based application for managing fund load restrictions in financial services. The project implements a system to adjudicate fund load attempts based on specified velocity limits and other controls, ensuring compliance with daily and weekly limits.

## Structure
- **funds/**: Main application module containing models, views, and business logic
- **settings/**: Django project configuration files
- **templates/**: HTML templates including Swagger UI
- **media/**: Static files for CSS, JavaScript, and API schema
- **docs/**: Documentation files
- **fixtures/**: Sample input data for testing

## Language & Runtime
**Language**: Python
**Version**: Python 3.13 (as noted in DEVELOPMENT.md)
**Framework**: Django 5.2.4
**Package Manager**: pip

## Dependencies
**Main Dependencies**:
- django==5.2.4

## Build & Installation
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

## API Documentation
The project includes Swagger UI for API documentation:
- **URL**: `/api/docs/`
- **Schema**: `/schema.yaml`

## Project Components

### Fund Load Processing
The core functionality processes fund load attempts with the following velocity limits:
- Daily Limit: $5,000 per day
- Weekly Limit: $20,000 per week
- Daily Load Count: Maximum 3 load attempts per day

### Input/Output Format
- **Input**: JSON format in `input.txt` with fund load attempts
- **Output**: JSON responses indicating whether loads were accepted or declined

### Testing
Tests can be run using Django's test framework:
```bash
python manage.py test
```

## Development Notes
The project was started with:
1. Creating a Django project: `django-admin startproject settings .`
2. Adding a Django app: `python manage.py startapp funds`
3. Setting up Swagger UI for API documentation