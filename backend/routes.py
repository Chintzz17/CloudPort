from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
import os

# Define the blueprint
main_bp = Blueprint('main_bp', __name__)

# Path to store user data (temporary file-based database)
USER_DATA_FILE = "backend/users.json"

# Helper function to load user data
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Helper function to save user data
def save_users(users):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(users, file, indent=4)


@main_bp.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@main_bp.route('/signup', methods=['POST'])
def handle_signup():
    users = load_users()

    full_name = request.form.get('full_name')
    email = request.form.get('email')
    password = request.form.get('password')
    employment_status = request.form.get('employment_status')
    gov_id = request.form.get('gov_id')
    tax_pin = request.form.get('tax_pin')
    phone1 = request.form.get('phone1')
    phone2 = request.form.get('phone2')

    if email in users:
        flash("Email already registered! Try logging in.", "error")
        return redirect(url_for('main_bp.signup'))

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
    flash("Account created successfully! Please log in.", "success")
    return redirect(url_for('main_bp.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()

        email = request.form.get('email')
        password = request.form.get('password')

        if email in users and users[email]['password'] == password:
            session['user_email'] = email
            session['user_name'] = users[email]['full_name']
            return redirect(url_for('main_bp.dashboard'))  # Redirect to a dashboard after login
        else:
            flash("Invalid credentials. Please try again.", "error")
            return redirect(url_for('main_bp.login'))

    return render_template('login.html')  

# Route: Dashboard (Example)
@main_bp.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('main_bp.login'))
    
    return render_template('dashboard.html',
                         user_name=session['user_name'],
                         user_email=session['user_email'])
    
    # return f"Welcome to your dashboard, {session['user']}!"

# Route: Logout
@main_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('main_bp.login'))