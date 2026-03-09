from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import smtplib
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, Flask, request, redirect, url_for, session, jsonify
from flask_login import login_user, LoginManager, UserMixin, current_user, login_required, logout_user
from flask import flash
from flask_mail import Mail, Message
import os
import hashlib
import joblib
import numpy as np
import pandas as pd
import json
import secrets
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'eza smart'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'img')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
app.config['MAIL_SUPPORT_RECIPIENT'] = os.getenv('MAIL_SUPPORT_RECIPIENT', app.config['MAIL_USERNAME'])

db = SQLAlchemy(app)
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

SENSOR_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'Models', 'ai_nutrient_analysis')
sensor_model = None
feature_scaler = None
crop_encoder = None
action_encoder = None
sensor_metadata = None

# Crop-specific optimal ranges for EC (mS/cm) and pH levels
CROP_OPTIMAL_RANGES = {
    'African Violet': {'ec_min': 1.2, 'ec_max': 1.5, 'ph_min': 6.0, 'ph_max': 7.0},
    'Basil': {'ec_min': 1.0, 'ec_max': 1.6, 'ph_min': 5.5, 'ph_max': 6.0},
    'Bean': {'ec_min': 2.0, 'ec_max': 4.0, 'ph_min': 6.0, 'ph_max': 6.0},
    'Banana': {'ec_min': 1.8, 'ec_max': 2.2, 'ph_min': 5.5, 'ph_max': 6.5},
    'Broccoli': {'ec_min': 2.8, 'ec_max': 3.5, 'ph_min': 6.0, 'ph_max': 6.8},
    'Cabbage': {'ec_min': 2.5, 'ec_max': 3.0, 'ph_min': 6.5, 'ph_max': 7.0},
    'Celery': {'ec_min': 1.8, 'ec_max': 2.4, 'ph_min': 6.5, 'ph_max': 6.5},
    'Carnation': {'ec_min': 2.0, 'ec_max': 3.5, 'ph_min': 6.0, 'ph_max': 6.0},
    'Courgettes': {'ec_min': 1.8, 'ec_max': 2.4, 'ph_min': 6.0, 'ph_max': 6.0},
    'Cucumber': {'ec_min': 1.7, 'ec_max': 2.0, 'ph_min': 5.0, 'ph_max': 5.5},
    'Eggplant': {'ec_min': 2.5, 'ec_max': 3.5, 'ph_min': 6.0, 'ph_max': 6.0},
    'Ficus': {'ec_min': 1.6, 'ec_max': 2.4, 'ph_min': 5.5, 'ph_max': 6.0},
    'Leek': {'ec_min': 1.4, 'ec_max': 1.8, 'ph_min': 6.5, 'ph_max': 7.0},
    'Lettuce': {'ec_min': 1.2, 'ec_max': 1.8, 'ph_min': 6.0, 'ph_max': 7.0},
    'Marrow': {'ec_min': 1.8, 'ec_max': 2.4, 'ph_min': 6.0, 'ph_max': 6.0},
    'Okra': {'ec_min': 2.0, 'ec_max': 2.4, 'ph_min': 6.5, 'ph_max': 6.5},
    'Pak Choi': {'ec_min': 1.5, 'ec_max': 2.0, 'ph_min': 7.0, 'ph_max': 7.0},
    'Peppers': {'ec_min': 0.8, 'ec_max': 1.8, 'ph_min': 5.5, 'ph_max': 6.0},
    'Parsley': {'ec_min': 1.8, 'ec_max': 2.2, 'ph_min': 6.0, 'ph_max': 6.5},
    'Rhubarb': {'ec_min': 1.6, 'ec_max': 2.0, 'ph_min': 5.5, 'ph_max': 6.0},
    'Rose': {'ec_min': 1.5, 'ec_max': 2.5, 'ph_min': 5.5, 'ph_max': 6.0},
    'Spinach': {'ec_min': 1.8, 'ec_max': 2.3, 'ph_min': 6.0, 'ph_max': 7.0},
    'Strawberry': {'ec_min': 1.8, 'ec_max': 2.2, 'ph_min': 6.0, 'ph_max': 6.0},
    'Sage': {'ec_min': 1.0, 'ec_max': 1.6, 'ph_min': 5.5, 'ph_max': 6.5},
    'Tomato': {'ec_min': 2.0, 'ec_max': 4.0, 'ph_min': 6.0, 'ph_max': 6.5},
}

def load_sensor_model():
    global sensor_model, feature_scaler, crop_encoder, action_encoder, sensor_metadata
    try:
        print("Loading sensor monitoring model...")
        sensor_model = joblib.load(os.path.join(SENSOR_MODEL_PATH, 'random_forest_model.pkl'))
        feature_scaler = joblib.load(os.path.join(SENSOR_MODEL_PATH, 'feature_scaler.pkl'))
        crop_encoder = joblib.load(os.path.join(SENSOR_MODEL_PATH, 'crop_encoder.pkl'))
        action_encoder = joblib.load(os.path.join(SENSOR_MODEL_PATH, 'action_encoder.pkl'))
        
        with open(os.path.join(SENSOR_MODEL_PATH, 'model_metadata.json'), 'r') as f:
            sensor_metadata = json.load(f)
        
        print("Sensor model loaded successfully")
    except Exception as e:
        print(f"Error loading sensor model: {e}")
        sensor_model = None

load_sensor_model()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.after_request
def add_header(response):
    response.cache_control.no_cache = True
    return response

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(50))
    gender = db.Column(db.String(50))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    profile_image_url = db.Column(db.String(200), nullable=True)
    profile_complete = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        """Generate a password reset token that expires in 1 hour"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiration = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Check if the reset token is valid and not expired"""
        if self.reset_token == token and self.reset_token_expiration > datetime.utcnow():
            return True
        return False
    
    def clear_reset_token(self):
        """Clear the reset token after use"""
        self.reset_token = None
        self.reset_token_expiration = None
        db.session.commit()

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('replies', lazy=True))
    
    def __repr__(self):
        return f'<Reply {self.id} to Post {self.post_id}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('posts', lazy=True))
    category = db.relationship('Category', backref=db.backref('posts', lazy=True))
    
    replies = db.relationship('Reply', backref='post', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Post {self.title}>'

def create_default_categories():
    if not Category.query.first():
        categories = [
            Category(name='General Discussion', description='A place for general, discussions or questions.'),
            Category(name='Introduction to Hydroponics', description='For beginners to learn about hydroponics.'),
            Category(name='Hydroponic Systems', description='Discussing different hydroponic systems like NFT, DWC, and aeroponics.'),
            Category(name='Nutrient Management', description='Learn how to manage nutrients in hydroponic farming.'),
            Category(name='Hydroponic Crops', description='Discuss the types of crops that thrive in hydroponics.'),
            Category(name='Technology in Hydroponics', description='Exploring technologies that aid hydroponic farming.'),
            Category(name='Sustainability in Hydroponics', description='Discussing how hydroponics contributes to sustainable farming.'),
            Category(name='Hydroponic Business Ideas', description='Discussing business opportunities in hydroponic farming.'),
        ]
        db.session.add_all(categories)
        db.session.commit()

def send_email(subject, recipient, body_html, body_text=None):
    """Send an email using Flask-Mail"""
    try:
        msg = Message(subject=subject,
                      recipients=[recipient],
                      html=body_html,
                      body=body_text if body_text else body_html)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_welcome_email(user):
    """Send a welcome email to newly registered users"""
    subject = "Welcome to FarmSmart!"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa; border-radius: 10px;">
            <h2 style="color: #28a745;">Welcome to FarmSmart, {user.username}!</h2>
            <p>Thank you for joining our hydroponic farming community!</p>
            <p>Your account has been successfully created. You can now:</p>
            <ul>
                <li>Access real-time sensor monitoring</li>
                <li>Get professional crop recommendations</li>
                <li>Connect with other farmers in our forums</li>
            </ul>
            <p>Get started by completing your profile and exploring our platform.</p>
            <p style="margin-top: 30px;">
                <a href="{url_for('dashboard', _external=True)}" 
                   style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Go to Dashboard
                </a>
            </p>
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                If you didn't create this account, please ignore this email.
            </p>
        </div>
    </body>
    </html>
    """
    return send_email(subject, user.email, html_body)

def send_password_reset_email(user, token):
    """Send password reset email with token"""
    reset_url = url_for('reset_password', token=token, _external=True)
    subject = "Password Reset Request - FarmSmart"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa; border-radius: 10px;">
            <h2 style="color: #007bff;">Password Reset Request</h2>
            <p>Hello {user.username},</p>
            <p>We received a request to reset your password for your FarmSmart account.</p>
            <p>Click the button below to reset your password. This link will expire in 1 hour.</p>
            <p style="margin-top: 30px;">
                <a href="{reset_url}" 
                   style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password
                </a>
            </p>
            <p style="color: #666; margin-top: 20px;">
                Or copy and paste this link into your browser:<br>
                <a href="{reset_url}">{reset_url}</a>
            </p>
            <p style="color: #dc3545; font-size: 14px; margin-top: 30px;">
                If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
            </p>
        </div>
    </body>
    </html>
    """
    return send_email(subject, user.email, html_body)

def send_password_changed_email(user):
    """Send confirmation email after password change"""
    subject = "Password Changed Successfully - FarmSmart"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa; border-radius: 10px;">
            <h2 style="color: #28a745;">Password Changed Successfully</h2>
            <p>Hello {user.username},</p>
            <p>This email confirms that your password was successfully changed.</p>
            <p>If you made this change, no further action is needed.</p>
            <p style="color: #dc3545; margin-top: 30px;">
                <strong>If you didn't make this change, please contact our support team immediately.</strong>
            </p>
            <p style="margin-top: 30px;">
                <a href="{url_for('login', _external=True)}" 
                   style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Login to Your Account
                </a>
            </p>
        </div>
    </body>
    </html>
    """
    return send_email(subject, user.email, html_body)

@app.route('/')
def home():
    return render_template('index.html', crop_ranges=CROP_OPTIMAL_RANGES)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


male_avatars = ['profilem1.jpg', 'profilem2.png']
female_avatars = ['profilew1.jpg', 'profilew2.jpeg', 'profilew3.jpeg']

def assign_avatar(gender):
    """Assign a random avatar based on gender."""
    if gender == 'Male':
        return random.choice(male_avatars)
    elif gender == 'Female':
        return random.choice(female_avatars)
    else:
        return 'default_avatar.jpg'  # Default avatar if gender is unspecified

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('form_type') == 'register':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role = 'farmer'
            gender = request.form.get('gender')

            if User.query.filter_by(username=username).first():
                flash('Username already taken. Please choose a different one.', 'error')
                return redirect(url_for('login') + '#register-form')
            if User.query.filter_by(email=email).first():
                flash('Email already registered. Please login or use a different email.', 'error')
                return redirect(url_for('login') + '#register-form')

            avatar_name = assign_avatar(gender)

            try:
                new_user = User(username=username, email=email, role=role, gender=gender, profile_image_url=avatar_name)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                
                # Send welcome email (non-blocking - don't fail signup if email fails)
                try:
                    send_welcome_email(new_user)
                except Exception as e:
                    print(f"Warning: Failed to send welcome email: {e}")
                
                flash('Registration successful! Please check your email for confirmation.')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                print(f"Registration error: {e}")
                flash('An error occurred during registration. Please try again.', 'error')
                return redirect(url_for('login') + '#register-form')

        elif request.form.get('form_type') == 'login':
            user = User.query.filter_by(email=request.form['email']).first()
            if user and user.check_password(request.form['password']):
                login_user(user)
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('forums'))

            flash("Invalid email or password. Please try again.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = user.generate_reset_token()
            
            if send_password_reset_email(user, token):
                flash('Password reset instructions have been sent to your email.', 'success')
            else:
                flash('Error sending email. Please try again later.', 'error')
        else:
            # Don't reveal if user exists or not (security best practice)
            flash('If that email exists in our system, you will receive password reset instructions.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired password reset link.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('reset_password.html', token=token)
        
        user.set_password(password)
        user.clear_reset_token()
        send_password_changed_email(user)
        
        flash('Your password has been reset successfully! Please log in with your new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username', current_user.username)
        email = request.form.get('email', current_user.email)
        address = request.form.get('address', current_user.address)
        phone = request.form.get('phone', current_user.phone)

        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate a unique filename using timestamp and user id
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"profile_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                current_user.profile_image_url = unique_filename
                flash('Profile image updated successfully!', 'success')

        current_user.username = username
        current_user.email = email
        current_user.address = address
        current_user.phone = phone
        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)

@app.route('/forums', methods=['GET', 'POST'])
@login_required
def forums():
    categories = Category.query.all()
    return render_template('forums.html', categories=categories)

@app.route('/category/<int:category_id>')
@login_required
def view_category(category_id):
    category = Category.query.get(category_id)
    if category:
        posts = Post.query.filter_by(category_id=category_id).all()
        return render_template('category-post.html', category=category, posts=posts, category_id=category_id)
    else:
        flash("Category not found.", 'danger')
        return redirect(url_for('home'))


@app.route('/category/<int:category_id>/posts', methods=['GET', 'POST'])
@login_required
def category_posts(category_id):
    category = Category.query.get_or_404(category_id)
    posts = Post.query.filter_by(category_id=category_id).all()

    if request.method == 'POST' and 'title' in request.form and 'content' in request.form:
        title = request.form['title']
        content = request.form['content']

        # Handle user ID: if the user is logged in, use their ID; else, handle anonymous posts
        user_id = current_user.id if current_user.is_authenticated else None
        
        new_post = Post(title=title, content=content, category_id=category.id, user_id=user_id)
        db.session.add(new_post)
        db.session.commit()

        flash('Post created successfully!', 'success')
        return redirect(url_for('category_posts', category_id=category.id))

    return render_template('category-post.html', category=category, posts=posts)

@app.route("/view_post/<int:post_id>")
@login_required
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    replies = Reply.query.filter_by(post_id=post_id).all()
    
    return render_template('view_post.html', post=post, replies=replies)


@app.route("/reply_to_post", methods=["POST"])
@login_required
def reply_to_post():
    content = request.form['reply_content']
    post_id = request.form['post_id']
    reply_author = request.form.get('reply_author')

    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = None
    
    reply = Reply(content=content, created_at=datetime.utcnow(), user_id=user_id, post_id=post_id)
    db.session.add(reply)
    db.session.commit()
    
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    if request.method == 'POST':
        if 'change_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not current_user.check_password(current_password):
                flash('Incorrect current password.', 'error')
            elif new_password != confirm_password:
                flash('New password and confirmation do not match.', 'error')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                
                # Send password change confirmation email
                try:
                    send_password_changed_email(current_user)
                except Exception as e:
                    print(f"Warning: Failed to send password change email: {e}")
                
                flash('Password updated successfully. A confirmation email has been sent.', 'success')

        elif 'delete_profile' in request.form:
            db.session.delete(current_user)
            db.session.commit()
            flash('Your account has been deleted successfully.', 'success')
            return redirect(url_for('login'))

        return redirect(url_for('account_settings'))

    return render_template('settings.html', user=current_user)
@app.route('/help')
def help():   
    return render_template('help.html', title="Help")


@app.route('/api/chat', methods=['POST'])
def chat():
    """EzaSmart Hydroponics Explainer Chatbot - answers questions about hydroponics."""
    try:
        data = request.get_json() or {}
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'response': 'Please ask a question about hydroponics!'}), 400
        
        try:
            from chatbot import get_chatbot
            chatbot = get_chatbot()
            response = chatbot.chat(message)
            return jsonify({'response': response}), 200
        except ImportError as ie:
            print(f"Chatbot import error: {ie}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'response': 'Chatbot module is unavailable. Please try again later or visit our Resources page.'
            }), 503
        except Exception as e:
            print(f"Chatbot error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'response': 'The chatbot encountered an error. Please try again or visit our Resources page for hydroponics information.'
            }), 500
    except Exception as e:
        print(f"Chat API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'response': 'An error occurred. Please try again.'}), 500

@app.route('/resources')
def resources():   
    return render_template('resources.html', title="Resources")


def _contact_fingerprint(name, email, subject, message):
    """Create a stable fingerprint for contact payload deduplication."""
    payload = "|".join([
        (name or "").strip().lower(),
        (email or "").strip().lower(),
        (subject or "").strip().lower(),
        (message or "").strip().lower(),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _is_duplicate_contact_submission(name, email, subject, message, window_seconds=20):
    """Prevent duplicate sends caused by accidental double-submit."""
    fingerprint = _contact_fingerprint(name, email, subject, message)
    now_ts = datetime.utcnow().timestamp()
    last_fp = session.get('last_contact_fingerprint')
    last_ts = float(session.get('last_contact_timestamp', 0))

    session['last_contact_fingerprint'] = fingerprint
    session['last_contact_timestamp'] = now_ts

    return last_fp == fingerprint and (now_ts - last_ts) < window_seconds

@app.route('/help/contact', methods=['POST'])
def send_support():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    if _is_duplicate_contact_submission(name, email, subject, message):
        flash('Duplicate submission detected. Please wait a moment before sending again.', 'info')
        return redirect(url_for('help'))

    full_message = f"""
    Subject: {subject}

    From: {name} <{email}>
    
    Message:
    {message}
    """

    try:
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as connection:
            if app.config['MAIL_USE_TLS']:
                connection.starttls()
            connection.login(user=app.config['MAIL_USERNAME'], password=app.config['MAIL_PASSWORD'])
            connection.sendmail(
                from_addr=app.config['MAIL_DEFAULT_SENDER'],
                to_addrs=app.config['MAIL_SUPPORT_RECIPIENT'],
                msg=full_message
            )
        flash('Your message has been sent successfully. Our team will get back to you shortly.', 'success')
    except Exception as e:
        flash(f"An error occurred while sending your message: {str(e)}", 'danger')

    return redirect(url_for('help'))
@app.route('/contact', methods=['POST'])
def send_contact_message():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject', 'Contact Form Submission')
    message = request.form.get('message')

    if _is_duplicate_contact_submission(name, email, subject, message):
        flash('Duplicate submission detected. Please wait a moment before sending again.', 'info')
        return redirect(url_for('home') + "#contact")

    full_message = f"""
    Subject: {subject}

    From: {name} <{email}>

    Message:
    {message}
    """

    try:
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as connection:
            if app.config['MAIL_USE_TLS']:
                connection.starttls()
            connection.login(user=app.config['MAIL_USERNAME'], password=app.config['MAIL_PASSWORD'])
            connection.sendmail(
                from_addr=app.config['MAIL_DEFAULT_SENDER'],
                to_addrs=app.config['MAIL_SUPPORT_RECIPIENT'],
                msg=f"Subject:{subject}\n\n{full_message}"
            )
        flash('Your message has been sent successfully. Our team will get back to you shortly.', 'success')
    except Exception as e:
        flash(f"An error occurred while sending your message: {str(e)}", 'danger')

    return redirect(url_for('home') + "#contact")

@app.route('/api/predict-sensor', methods=['POST'])
def predict_sensor():
    """API endpoint for sensor data prediction with crop-specific recommendations"""
    try:
        data = request.get_json()
        crop_id = data.get('crop_id', '').strip()
        ph_level = float(data.get('ph_level', 0))
        ec_value = float(data.get('ec_value', 0))
        ambient_temp = float(data.get('ambient_temp', 0))
        
        if not crop_id or ph_level == 0 or ec_value == 0 or ambient_temp == 0:
            return jsonify({
                'success': False,
                'error': 'Please provide all required sensor readings.'
            }), 400
        
        # Check if model is loaded
        if sensor_model is None or feature_scaler is None or crop_encoder is None or action_encoder is None:
            return jsonify({
                'success': False,
                'error': 'Sensor model is not available at the moment. Please try again later.'
            }), 503
        
        try:
            crop_encoded = crop_encoder.transform([crop_id])[0]
        except:
            return jsonify({
                'success': False,
                'error': f'Invalid crop type. Supported crops: {", ".join(sensor_metadata["crop_classes"])}'
            }), 400
        

        crop_ranges = CROP_OPTIMAL_RANGES.get(crop_id, {})
        ec_min = crop_ranges.get('ec_min', 1.2)
        ec_max = crop_ranges.get('ec_max', 2.4)
        ph_min = crop_ranges.get('ph_min', 5.5)
        ph_max = crop_ranges.get('ph_max', 6.5)
        
        # Prepare features with proper column names to match training data
        feature_names = ['Crop_ID_encoded', 'pH_Level', 'EC_Value', 'Ambient_Temp']
        features = pd.DataFrame(
            [[crop_encoded, ph_level, ec_value, ambient_temp]],
            columns=feature_names
        )
        
        features_scaled_array = feature_scaler.transform(features)
        features_scaled = pd.DataFrame(features_scaled_array, columns=feature_names)
        prediction = sensor_model.predict(features_scaled)
        action = action_encoder.inverse_transform(prediction)[0]
        
        # Validate and override action based on actual sensor readings vs optimal ranges
        # This ensures the recommendation is logically correct for the crop's needs
        if ph_min <= ph_level <= ph_max and ec_min <= ec_value <= ec_max:
            action = 'Maintain'
        elif ec_value < ec_min:
            action = 'Add_Nutrients'
        elif ec_value > ec_max:
            action = 'Dilute'
        elif ph_level < ph_min:
            action = 'Add_pH_Up'
        elif ph_level > ph_max:
            action = 'Add_pH_Down'
        
        description = generate_crop_specific_recommendation(
            action=action,
            crop=crop_id,
            ph_level=ph_level,
            ec_value=ec_value,
            ph_min=ph_min,
            ph_max=ph_max,
            ec_min=ec_min,
            ec_max=ec_max
        )
        
        return jsonify({
            'success': True,
            'action': action,
            'description': description,
            'inputs': {
                'crop': crop_id,
                'pH': ph_level,
                'EC': ec_value,
                'Temperature': ambient_temp,
                'pH_Range': f'{ph_min}-{ph_max}',
                'EC_Range': f'{ec_min}-{ec_max} mS/cm'
            }
        }), 200
        
    except Exception as e:
        print(f"Error predicting sensor data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'An error occurred while analyzing sensor data. Please try again.'
        }), 500


def generate_crop_specific_recommendation(action, crop, ph_level, ec_value, ph_min, ph_max, ec_min, ec_max):
    """Generate a dynamic, crop-specific recommendation based on sensor readings and optimal ranges"""
    
    if action == 'Add_pH_Up':
        return f"""<strong>pH Level Too Low for {crop}</strong><br><br>
        Your current pH is <strong>{ph_level}</strong>, but {crop} thrives at pH <strong>{ph_min}-{ph_max}</strong>.<br><br>
        <strong>Action:</strong> Add pH Up solution (potassium hydroxide or potassium carbonate) gradually—start with 1ml per gallon of nutrient solution. 
        Mix thoroughly, wait 15 minutes, then retest pH. Repeat if needed until pH reaches {ph_min}-{ph_max}."""
    
    elif action == 'Add_pH_Down':
        return f"""<strong>pH Level Too High for {crop}</strong><br><br>
        Your current pH is <strong>{ph_level}</strong>, but {crop} thrives at pH <strong>{ph_min}-{ph_max}</strong>.<br><br>
        <strong>Action:</strong> Add pH Down solution (phosphoric acid or citric acid) gradually—start with 1ml per gallon of nutrient solution. 
        Mix thoroughly, wait 15 minutes, then retest pH. Repeat if needed until pH reaches {ph_min}-{ph_max}."""
    
    elif action == 'Add_Nutrients':
        return f"""<strong>Nutrient Level Too Low for {crop}</strong><br><br>
        Your current EC is <strong>{ec_value} mS/cm</strong>, but {crop} requires an EC of <strong>{ec_min}-{ec_max} mS/cm</strong>.<br><br>
        <strong>Action:</strong> Add your hydroponic nutrient concentrate following the manufacturer's feeding chart for {crop}. 
        Start with half the recommended dose, mix well, wait 30 minutes, then retest EC. Your target is {ec_min}-{ec_max} mS/cm."""
    
    elif action == 'Dilute':
        return f"""<strong>Nutrient Level Too High for {crop}</strong><br><br>
        Your current EC is <strong>{ec_value} mS/cm</strong>, but {crop} requires an EC of <strong>{ec_min}-{ec_max} mS/cm</strong>. 
        This concentration is excessively high.<br><br>
        <strong>Action:</strong> Remove 20-30% of your current nutrient solution and replace with fresh pH-balanced water (pH {ph_min}-{ph_max}). 
        Mix thoroughly, wait 30 minutes, then retest EC. Repeat if needed until EC drops to {ec_min}-{ec_max} mS/cm."""
    
    elif action == 'Maintain':
        return f"""<strong>Excellent! {crop} Conditions Optimal</strong><br><br>
        Your readings are perfect for {crop}:<br>
        • pH: <strong>{ph_level}</strong> (Target: {ph_min}-{ph_max})<br>
        • EC: <strong>{ec_value} mS/cm</strong> (Target: {ec_min}-{ec_max})<br><br>
        <strong>Action:</strong> Continue monitoring these parameters daily. Top up water as needed to maintain nutrient levels. 
        Change your reservoir completely every 2 weeks to prevent nutrient imbalances and pathogen buildup."""
    
    else:
        return f"Follow standard monitoring procedures for {crop}. Target pH: {ph_min}-{ph_max}, Target EC: {ec_min}-{ec_max} mS/cm"

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# Initialize database on app startup (called by gunicorn on Render)
with app.app_context():
    try:
        print("Initializing database...")
        db.create_all()  # Creates tables if they don't exist
        create_default_categories()  # Adds default forum categories
        print("Database initialized successfully")
    except Exception as e:
        print(f"⚠ Warning: Database initialization error: {e}")


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5010)
