import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "paraffin.db")
DEBUG = True
SECRET_KEY = "paraffin-wax-dev-key"
