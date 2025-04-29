# Energy Finance Django Application

## Overview
The Energy Finance application is a powerful tool for financial analysis of energy projects with a focus on solar power. 
It helps energy analysts evaluate project viability through financial metrics and risk assessment.

## Features
- Project management with detailed financial parameters
- Solar project analysis with technical specifications
- Cash flow projections and financial metrics (IRR, NPV, LCOE)
- Risk assessment based on country, technology, project status, and off-taker ratings
- Integration with NREL's PVWatts API for solar radiation data
- Machine learning models for power generation prediction

## Setup Instructions

### Install Requirements
```bash
pip install -r requirements.txt
```

### Configure Database
Update the `settings.py` file with your database configuration or set the following environment variables:
- `DATABASE_URL`: Your database connection string

### Initialize Database
```bash
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Run Development Server
```bash
python manage.py runserver
```

## API Keys
For solar radiation data, you'll need to obtain an API key from NREL:
1. Visit https://developer.nrel.gov/signup/
2. Register and get your API key
3. Set it as an environment variable: `NREL_API_KEY`

## License
Copyright (c) 2025 Sustains.ai
