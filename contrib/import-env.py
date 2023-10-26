import os
from dotenv import load_dotenv

try:
    load_dotenv()  # Load environment variables from a .env file
except Exception as e:
    print(f"Error loading .env file: {e}")