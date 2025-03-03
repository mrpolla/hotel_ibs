from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
db = SQLAlchemy(app)

from models import Chain, Hotel  # Import all your models

if __name__ == '__main__':
    app.run(debug=True)