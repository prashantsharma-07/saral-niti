from flask import Flask, render_template  # ← render_template ADD kiya
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import os


# Load .env file
load_dotenv()

# ← template_folder aur static_folder ADD kiya
app = Flask(__name__,
    template_folder='templates',
    static_folder='static'
)
CORS(app)

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI")
if MONGO_URI:
    client = MongoClient(MONGO_URI)
else:
    client = None
db = client["saral_niti_db"] if client is not None else None
schemes_collection = db["schemes"] if db is not None else None

# ← pehle JSON return karta tha, ab HTML page serve karta hai
@app.route("/")
def home():
    return render_template("base.html")  # ← CHANGE kiya

@app.route("/schemes")
def schemes_page():
    return render_template("schemes.html")

@app.route("/project")
def project_page():
    return render_template("project.html")
# MongoDB connection test — kuch nahi badla
@app.route("/test-db")
def test_db():
    try:
        client.admin.command("ping")
        count = schemes_collection.count_documents({})
        return {
            "message": "MongoDB connected successfully",
            "schemes_in_db": count,
            "status": "ok"
        }
    except Exception as e:
        return {"message": "MongoDB connection failed", "error": str(e)}, 500

# Register blueprints — kuch nahi badla
from routes.schemes import schemes_bp
from routes.search import search_bp
from routes.filter import filter_bp
from routes.live import live_bp
from routes.chatbot import chatbot_bp
from routes.detector import detector_bp

app.register_blueprint(schemes_bp)
app.register_blueprint(search_bp)
app.register_blueprint(filter_bp)
app.register_blueprint(live_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(detector_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)