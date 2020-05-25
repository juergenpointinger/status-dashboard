import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Debug mode
DEBUG=os.getenv('DEBUG', 0)
# Logging level
LOGLEVEL=os.getenv('LOGLEVEL', 'INFO')
# Logging format
LOGFORMAT=os.getenv('LOGFORMAT', '%(asctime)s - %(levelname)s - %(message)s')

# Dash application name
APP_NAME=os.getenv('APP_NAME', 'Status Dashboard')
# Dash host ip adress
APP_HOST=os.getenv('APP_HOST', '127.0.0.1')
# Dash application folder
APP_ROOT=os.getcwd()
# Dash server port
APP_PORT=os.getenv('APP_PORT')

# External css
FONTAWESOME='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.13.0/css/all.min.css'

# GitLab URL
GITLAB_API_URL=os.getenv('GITLAB_API_URL', 'https://gitlab.com/api/v4')
# GitLab token will be used whenever the API is invoked
GITLAB_TOKEN=os.getenv('GITLAB_TOKEN')
# GitLab group id
GITLAB_GROUP_ID=os.getenv('GITLAB_GROUP_ID')
# GitLab project ids
GITLAB_PROJECT_IDS=os.getenv('GITLAB_PROJECT_IDS').split(',')