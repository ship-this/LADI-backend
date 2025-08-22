import os
import logging
from app import create_app
# from app.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ladi_app.log')
    ]
)

# Get configuration
config_name = os.getenv('FLASK_ENV', 'development')
# app_config = Config[config_name]

# Create Flask app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False) 