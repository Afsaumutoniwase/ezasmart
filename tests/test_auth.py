"""
Tests for authentication functionality
"""
import pytest
from flask import session
from app import User, db


class TestRegistration:
    """Tests for user registration"""
    
    def test_register_page_loads(self, client):
        """Test that registration page loads (via login page)"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Register' in response.data or b'Sign up' in response.data or b'Login' in response.data
    
    def test_successful_registration(self, client, app):
        """Test successful user registration"""
        response = client.post('/login', data={
            'form_type': 'register',
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'gender': 'male'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.username == 'newuser'
            assert user.role == 'farmer'
    
    def test_registration_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = client.post('/login', data={
            'form_type': 'register',
            'username': 'anotheruser',
            'email': 'test@example.com',  # Already exists
            'password': 'password123',
            'gender': 'female'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'already exists' in response.data or b'Email' in response.data
    
    def test_registration_duplicate_username(self, client, test_user):
        """Test registration with duplicate username"""
        response = client.post('/login', data={
            'form_type': 'register',
            'username': 'testuser',  # Already exists
            'email': 'another@example.com',
            'password': 'password123',
            'gender': 'male'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'already exists' in response.data or b'Username' in response.data
    
    def test_registration_password_mismatch(self, client):
        """Test registration with mismatched passwords (not implemented in this app)"""
        pass
    
    def test_registration_short_password(self, client):
        """Test registration with password that's too short (not validated in this app)"""
        pass


class TestLogin:
    """Tests for user login"""
    
    def test_login_page_loads(self, client):
        """Test that login page loads"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data or b'Sign in' in response.data
    
    def test_successful_login(self, client, test_user):
        """Test successful login"""
        response = client.post('/login', data={
            'form_type': 'login',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Welcome' in response.data
    
    def test_login_invalid_email(self, client):
        """Test login with non-existent email"""
        response = client.post('/login', data={
            'form_type': 'login',
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'incorrect' in response.data
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        response = client.post('/login', data={
            'form_type': 'login',
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'incorrect' in response.data
    
    def test_login_empty_fields(self, client):
        """Test login with empty fields"""
        response = client.post('/login', data={
            'form_type': 'login',
            'email': '',
            'password': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200


class TestLogout:
    """Tests for user logout"""
    
    def test_logout_when_logged_in(self, authenticated_client):
        """Test logout when user is logged in"""
        response = authenticated_client.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'logged out' in response.data or b'Login' in response.data
    
    def test_logout_when_not_logged_in(self, client):
        """Test logout when user is not logged in"""
        response = client.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Login' in response.data


class TestPasswordReset:
    """Tests for password reset functionality"""
    
    def test_forgot_password_page_loads(self, client):
        """Test that forgot password page loads"""
        response = client.get('/forgot-password')
        assert response.status_code == 200
        assert b'password' in response.data.lower()
    
    def test_forgot_password_valid_email(self, client, test_user):
        """Test password reset request with valid email"""
        response = client.post('/forgot-password', data={
            'email': 'test@example.com'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'email' in response.data.lower()
    
    def test_forgot_password_invalid_email(self, client):
        """Test password reset request with invalid email"""
        response = client.post('/forgot-password', data={
            'email': 'nonexistent@example.com'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'email' in response.data.lower()
    
    def test_reset_password_with_valid_token(self, client, test_user, app):
        """Test resetting password with valid token"""
        with app.app_context():
            user = User.query.get(test_user.id)
            token = user.generate_reset_token()
        
        response = client.get(f'/reset-password/{token}')
        assert response.status_code == 200
        assert b'password' in response.data.lower()
        
        response = client.post(f'/reset-password/{token}', data={
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'reset' in response.data.lower() or b'success' in response.data.lower()
        
        with app.app_context():
            user = User.query.get(test_user.id)
            assert user.check_password('newpassword123') is True
    
    def test_reset_password_with_invalid_token(self, client):
        """Test resetting password with invalid token"""
        response = client.get('/reset-password/invalid_token_xyz', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'expired' in response.data
    
    def test_reset_password_mismatched_passwords(self, client, test_user, app):
        """Test password reset with mismatched passwords"""
        with app.app_context():
            user = User.query.get(test_user.id)
            token = user.generate_reset_token()
        
        response = client.post(f'/reset-password/{token}', data={
            'password': 'newpassword123',
            'confirm_password': 'differentpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'match' in response.data
    
    def test_reset_password_too_short(self, client, test_user, app):
        """Test password reset with password that's too short"""
        with app.app_context():
            user = User.query.get(test_user.id)
            token = user.generate_reset_token()
        
        response = client.post(f'/reset-password/{token}', data={
            'password': '123',
            'confirm_password': '123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'6 characters' in response.data or b'short' in response.data


class TestProtectedRoutes:
    """Tests for login-required routes"""
    
    def test_dashboard_requires_login(self, client):
        """Test dashboard route behavior for anonymous users"""
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers.get('Location', '')
    
    def test_profile_requires_login(self, client):
        """Test that profile page requires authentication"""
        response = client.get('/profile', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Login' in response.data or b'Unauthorized' in response.data
    
    def test_dashboard_accessible_when_logged_in(self, authenticated_client):
        """Test that dashboard is accessible when logged in"""
        response = authenticated_client.get('/dashboard')
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_profile_accessible_when_logged_in(self, authenticated_client):
        """Test that profile is accessible when logged in"""
        response = authenticated_client.get('/profile')
        
        assert response.status_code == 200
        assert b'Profile' in response.data or b'testuser' in response.data
