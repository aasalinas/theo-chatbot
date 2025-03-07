from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import sqlite3
import os
from dotenv import load_dotenv
import openai
from weather_handler import get_weather
from email_handler import send_email
from serpapi import GoogleSearch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import uuid
import re
import google.auth
from flask_wtf.csrf import CSRFProtect

# ✅ Load API Keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERP_API_KEY = os.getenv("SERPAPI_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# ✅ Initialize Flask App
app = Flask(__name__)
app.secret_key = "your_secret_key"
client = openai.OpenAI()
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ✅ Initialize CSRF Protection
csrf = CSRFProtect(app)

@app.before_request
def disable_csrf_for_ngrok():
    if "ngrok" in request.host_url:
        setattr(request, "_disable_csrf", True)


# ✅ Load API Keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERP_API_KEY = os.getenv("SERPAPI_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# ✅ Initialize Flask App
app = Flask(__name__)
app.secret_key = "your_secret_key"
client = openai.OpenAI()
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ✅ Initialize SQLite Databases
def init_db():
    conn = sqlite3.connect("chat_memory.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            bot_response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def init_user_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# ✅ User Class
class User(UserMixin):
    def __init__(self, id, username):
        self.id = str(id)  # Ensure ID is a string for Flask-Login
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (int(user_id),))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return User(id=user[0], username=user[1])
    return None

# ✅ Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        
        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Username already exists"
    return render_template("register.html")

# ✅ Logout Route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ✅ Home Route (Protected)
@app.route("/")
def home():
    if current_user.is_authenticated:
        return render_template("index.html", username=current_user.username)
    return "Welcome! Please <a href='/login'>log in</a> to continue."

# ✅ Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return "Username and password are required", 400

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[1], password):
            user_obj = User(id=user[0], username=username)
            login_user(user_obj)
            return redirect(url_for("home"))
        return "Invalid username or password", 400

    return render_template("login.html")

# ✅ Fetch Live Google Search Results
def get_google_search_results(query):
    if not query:
        return "**Please provide a search query.**"
    try:
        params = {
            "q": query,
            "hl": "en",
            "gl": "us",
            "api_key": SERP_API_KEY
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        if "organic_results" not in results:
            return "**No search results found.**"
        search_results = results["organic_results"]
        formatted_results = "<b>📰 Latest AI News:</b><br><br><ul>"
        for index, result in enumerate(search_results[:5]):
            title = result.get("title", "No Title")
            link = result.get("link", "#")
            snippet = result.get("snippet", "No description available.")
            formatted_results += f"""
            <li>
                <b>{index+1}. <a href='{link}' target='_blank'>{title}</a></b><br>
                📝 {snippet}<br><br>
            </li>
            """
        formatted_results += "</ul>"
        return formatted_results
    except Exception as e:
        print(f"❌ Error fetching Google search results: {e}")
        return "**An error occurred while fetching search results.**"

# ✅ Chat Route
@app.route("/chat", methods=["POST"])
@login_required
def chat():
    try:
        data = request.get_json()
        user_message = data["message"].lower()
        print(f"✅ Received message: {user_message}")
        if "latest news" in user_message or "ai news" in user_message:
            search_query = "latest AI news"
            return jsonify({"response": get_google_search_results(search_query)})
        if "weather in" in user_message or "forecast for" in user_message:
            city = user_message.replace("weather in", "").replace("forecast for", "").strip()
            return jsonify({"response": get_weather(city)})
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        return jsonify({"response": response.choices[0].message.content})
    except google.auth.exceptions.GoogleAuthError:
        return jsonify({"response": "Google Authentication Error: Check credentials."}), 500
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return jsonify({"response": f"Error: {str(e)}"}), 500

# ✅ Run Flask App
if __name__ == "__main__":
    init_db()
    init_user_db()
    app.run(host="0.0.0.0", port=5000, debug=True)