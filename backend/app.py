import os
import json
import logging
from flask import Flask, redirect, url_for, request, flash, session, render_template, jsonify
from recommendation_engine import RecommendationEngine  # New import
from werkzeug.utils import secure_filename

# Configure upload folder


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

    UPLOAD_FOLDER = 'static/images'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit

    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            employment_status = request.form.get('employment_status')
            gov_id = request.form.get('gov_id')
            tax_pin = request.form.get('tax_pin')
            phone1 = request.form.get('phone1')
            phone2 = request.form.get('phone2')

            users = load_users()

            if email in users:
                flash('Email already registered. Please log in.', 'error')
                return redirect(url_for('login'))

            users[email] = {
                "full_name": full_name,
                "password": password,
                "employment_status": employment_status,
                "gov_id": gov_id,
                "tax_pin": tax_pin,
                "phone1": phone1,
                "phone2": phone2
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
    
    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        if 'user_email' not in session:
            flash('Please log in to view your profile.', 'error')
            return redirect(url_for('login'))
        
        users = load_users()
        user_email = session['user_email']
        
        if user_email not in users:
            flash('User not found.', 'error')
            return redirect(url_for('logout'))
        
        if request.method == 'POST':
            # Handle file upload
            if 'profile_photo' in request.files:
                file = request.files['profile_photo']
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{user_email}_{file.filename}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    users[user_email]['profile_photo'] = filename
            
            # Update other profile info
            users[user_email].update({
                "full_name": request.form.get('full_name'),
                "employment_status": request.form.get('employment_status'),
                "phone1": request.form.get('phone1'),
                "phone2": request.form.get('phone2'),
                "gov_id": request.form.get('gov_id'),
                "tax_pin": request.form.get('tax_pin')
            })
            
            save_users(users)
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        
        # Add email to user_info for display
        user_info = users[user_email]
        user_info['email'] = user_email
        return render_template("profile.html", user_info=user_info)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)