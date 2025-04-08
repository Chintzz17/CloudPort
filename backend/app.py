import os
import json
import logging
from flask import Flask, redirect, url_for, request, flash, session, render_template, jsonify
from recommendation_engine import RecommendationEngine  # New import

def create_app():
    """Initialize the Flask application with configurations and routes."""
    app = Flask(__name__)

    # Load configurations
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Get the directory where app.py is located
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to users.json
    USERS_FILE = os.path.join(BASE_DIR, 'users.json')

    # Log the path to users.json
    logging.info(f"Loading users from: {USERS_FILE}")

    # Initialize Recommendation Engine (NEW)
    rec_engine = RecommendationEngine()

    def load_users():
        """Load users from the users.json file."""
        if not os.path.exists(USERS_FILE):
            # Create the file if it doesn't exist
            with open(USERS_FILE, 'w') as file:
                json.dump({}, file)  # Initialize with an empty dictionary
            return {}

        with open(USERS_FILE, 'r') as file:
            return json.load(file)

    def save_users(users):
        """Save users to the users.json file."""
        with open(USERS_FILE, 'w') as file:
            json.dump(users, file, indent=4)

    # Login Route
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            # Load users from the file
            users = load_users()

            # Check if the user exists and the password is correct
            if email in users and users[email]["password"] == password:
                # Store user email in session to indicate they are logged in
                session['user_email'] = email
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password. Please try again.', 'error')
                return redirect(url_for('login'))

        return render_template('login.html')

    # Signup Route
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            password = request.form.get('password')

            # Load existing users
            users = load_users()

            # Check if the email is already registered
            if email in users:
                flash('Email already registered. Please log in.', 'error')
                return redirect(url_for('login'))

            # Save the new user
            users[email] = {
                "full_name": full_name,
                "password": password,
            }
            save_users(users)

            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))

        return render_template('signup.html')

    # Dashboard Route
    @app.route('/dashboard')
    def dashboard():
        # Check if the user is logged in
        if 'user_email' not in session:
            flash('Please log in to access the dashboard.', 'error')
            return redirect(url_for('login'))

        # Load users from the file
        users = load_users()

        # Fetch user data
        user_email = session['user_email']
        user_name = users[user_email]["full_name"]

        return render_template('dashboard.html', user_name=user_name, user_email=user_email)

    # Recommendation Route (NEW)
    @app.route('/recommend', methods=['POST'])
    def recommend():
        if 'user_email' not in session:
            return jsonify({'error': 'Please login first'}), 401

        try:
            data = request.get_json()
            if not data or 'course' not in data or 'level' not in data:
                return jsonify({'error': 'Missing course or level'}), 400

            recommendations = rec_engine.recommend_courses(data)
            return jsonify({'recommendations': recommendations})
        except Exception as e:
            logging.error(f"Recommendation error: {str(e)}")
            return jsonify({'error': 'Server error'}), 500

    # Logout Route
    @app.route('/logout')
    def logout():
        # Clear the session to log the user out
        session.pop('user_email', None)
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)