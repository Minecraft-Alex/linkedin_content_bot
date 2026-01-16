# LinkedIn Content Bot

An AI-powered content bot that automatically scrapes web content and posts it to LinkedIn.

## Features
- Automated web scraping of specified topics
- Content filtering and refinement
- Scheduled posting to LinkedIn
- Customizable posting templates
- Logging and monitoring

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your LinkedIn credentials
4. Update `config/config.yaml` with your preferences
5. Run `python src/main.py`

## Configuration
Update `config/config.yaml` with:
- Search topics
- Posting schedule
- Content filters
- LinkedIn posting preferences

## Environment Variables
Create a `.env` file in the root directory with:
```
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

## Usage
Run the bot with:
```bash
python src/main.py
```

The bot will automatically:
1. Scrape content from configured sources
2. Filter content based on your criteria
3. Post to LinkedIn according to the schedule
4. Log all activities for monitoring

## Logging
All bot activities are logged in the `logs` directory.
