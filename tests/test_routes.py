"""
Tests for application routes
"""
import pytest
import types
from unittest.mock import patch
from app import User, Category, Post, Reply, db


class TestHomeRoute:
    """Tests for the home/index route"""
    
    def test_home_page_loads(self, client):
        """Test that home page loads successfully"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'FarmSmart' in response.data or b'Hydroponic' in response.data
    
    def test_home_page_has_crop_ranges(self, client):
        """Test that home page includes crop reference data"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Tomato' in response.data or b'Lettuce' in response.data or b'Basil' in response.data


class TestDashboardRoute:
    """Tests for the dashboard route"""
    
    def test_dashboard_requires_auth(self, client):
        """Test dashboard route behavior for anonymous users"""
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers.get('Location', '')
    
    def test_dashboard_accessible_when_logged_in(self, authenticated_client):
        """Test that authenticated users can access dashboard"""
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Nutrient' in response.data


class TestProfileRoute:
    """Tests for the profile route"""
    
    def test_profile_get_requires_auth(self, client):
        """Test that profile page requires authentication"""
        response = client.get('/profile', follow_redirects=True)
        assert response.status_code == 200
        assert b'Login' in response.data
    
    def test_profile_shows_user_info(self, authenticated_client, test_user, app):
        """Test that profile page shows user information"""
        response = authenticated_client.get('/profile')
        assert response.status_code == 200
        assert b'testuser' in response.data
        assert b'test@example.com' in response.data
    
    def test_profile_update(self, authenticated_client, test_user, app):
        """Test updating profile"""
        response = authenticated_client.post('/profile', data={
            'username': 'updateduser',
            'email': 'updated@example.com',
            'address': '789 Updated Street',
            'phone': '5555555555'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'success' in response.data.lower() or b'updated' in response.data.lower()

        with app.app_context():
            user = User.query.get(test_user.id)
            assert user.username == 'updateduser'
            assert user.email == 'updated@example.com'
            assert user.phone == '5555555555'


class TestForumsRoute:
    """Tests for forums functionality"""
    
    def test_forums_page_loads(self, authenticated_client, test_categories):
        """Test that forums page loads"""
        response = authenticated_client.get('/forums')
        assert response.status_code == 200
        assert b'Forum' in response.data or b'Discussion' in response.data
    
    def test_forums_shows_categories(self, authenticated_client, test_categories):
        """Test that forums page shows categories"""
        response = authenticated_client.get('/forums')
        assert response.status_code == 200
        assert b'General Discussion' in response.data
    
    def test_view_category(self, authenticated_client, test_categories):
        """Test viewing a specific category"""
        category_id = test_categories[0]
        response = authenticated_client.get(f'/category/{category_id}')
        assert response.status_code == 200
        assert b'General Discussion' in response.data
    
    def test_view_invalid_category(self, client):
        """Test viewing a non-existent category"""
        response = client.get('/category/99999', follow_redirects=True)
        assert response.status_code == 200
    
    def test_create_post_requires_auth(self, client, test_categories):
        """Test creating post anonymously redirects to login"""
        category_id = test_categories[0]
        response = client.post(f'/category/{category_id}/posts', data={
            'title': 'Test Post',
            'content': 'Test content'
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers.get('Location', '')
    
    def test_create_post_when_authenticated(self, authenticated_client, test_categories, app):
        """Test creating a post when authenticated"""
        category_id = test_categories[0]
        response = authenticated_client.post(f'/category/{category_id}/posts', data={
            'title': 'New Forum Post',
            'content': 'This is my new post content'
        }, follow_redirects=True)
        
        assert response.status_code == 200

        with app.app_context():
            post = Post.query.filter_by(title='New Forum Post').first()
            assert post is not None
            assert post.content == 'This is my new post content'
    
    def test_view_post(self, authenticated_client, test_post):
        """Test viewing a specific post"""
        response = authenticated_client.get(f'/view_post/{test_post}')
        assert response.status_code == 200
        assert b'Test Post' in response.data
    
    def test_create_reply_requires_auth(self, client, test_post):
        """Test that creating a reply anonymously redirects to login"""
        response = client.post('/reply_to_post', data={
            'reply_content': 'Test reply',
            'post_id': test_post
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers.get('Location', '')
    
    def test_create_reply_when_authenticated(self, authenticated_client, test_post, app):
        """Test creating a reply when authenticated"""
        response = authenticated_client.post('/reply_to_post', data={
            'reply_content': 'This is my reply to the post',
            'post_id': test_post
        }, follow_redirects=True)
        
        assert response.status_code == 200

        with app.app_context():
            reply = Reply.query.filter_by(content='This is my reply to the post').first()
            assert reply is not None
            assert reply.post_id == test_post

    def test_delete_post_redirects_to_view_category(self, client, app, test_user, test_post):
        """Test post deletion redirects to the existing category view endpoint."""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            user.role = 'admin'
            db.session.commit()

            post = Post.query.get(test_post)
            category_id = post.category_id

        with client:
            client.post('/login', data={
                'form_type': 'login',
                'email': 'test@example.com',
                'password': 'testpassword123'
            }, follow_redirects=True)

            response = client.post(f'/admin/post/{test_post}/delete', follow_redirects=False)

        assert response.status_code == 302
        assert f'/category/{category_id}' in response.headers.get('Location', '')


class TestResourcesRoute:
    """Tests for resources page"""
    
    def test_resources_page_loads(self, client):
        """Test that resources page loads"""
        response = client.get('/resources')
        assert response.status_code == 200
        assert b'Resource' in response.data or b'Video' in response.data or b'Learning' in response.data


class TestHelpRoute:
    """Tests for help/support page"""
    
    def test_help_page_loads(self, client):
        """Test that help page loads"""
        response = client.get('/help')
        assert response.status_code == 200
        assert b'Help' in response.data or b'Support' in response.data or b'Contact' in response.data


class TestSettingsRoute:
    """Tests for settings page"""
    
    def test_settings_requires_auth(self, client):
        """Test that settings requires authentication"""
        response = client.get('/settings', follow_redirects=True)
        assert b'Login' in response.data or response.status_code == 401 or response.status_code == 404

    def test_settings_change_password_validation(self, authenticated_client):
        """Test settings password validation path"""
        response = authenticated_client.post('/settings', data={
            'change_password': '1',
            'current_password': 'wrong-password',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestHydroponicRoute:
    """Tests for hydroponic systems page"""
    
    def test_hydroponic_page_loads(self, client):
        """Test that hydroponic section exists on home page"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Hydroponic' in response.data or b'System' in response.data


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_page(self, client):
        """Test that 404 errors are handled"""
        response = client.get('/nonexistent-page-xyz')
        assert response.status_code in [200, 404]
    
    def test_invalid_post_id(self, authenticated_client):
        """Test accessing non-existent post"""
        response = authenticated_client.get('/view_post/99999')
        assert response.status_code == 404


class TestCommunicationRoutes:
    """Tests for chat and contact routes"""

    def test_chat_empty_message(self, client):
        response = client.post('/api/chat', json={'message': ''})
        assert response.status_code == 400

    def test_chat_message_with_mocked_bot(self, client):
        fake_bot = types.SimpleNamespace(chat=lambda message: 'Test reply')
        fake_module = types.SimpleNamespace(get_chatbot=lambda: fake_bot)
        with patch.dict('sys.modules', {'chatbot': fake_module}):
            response = client.post('/api/chat', json={'message': 'How do I test?'})
        assert response.status_code == 200
        payload = response.get_json()
        assert payload['response'] == 'Test reply'

    def test_help_contact_submission(self, client):
        smtp_mock = patch('smtplib.SMTP').start()
        smtp_mock.return_value.__enter__.return_value = smtp_mock.return_value
        try:
            response = client.post('/help/contact', data={
                'name': 'Tester',
                'email': 'tester@example.com',
                'subject': 'Need help',
                'message': 'Testing support form'
            })
            assert response.status_code == 302
        finally:
            patch.stopall()

    def test_home_contact_submission(self, client):
        smtp_mock = patch('smtplib.SMTP').start()
        smtp_mock.return_value.__enter__.return_value = smtp_mock.return_value
        try:
            response = client.post('/contact', data={
                'name': 'Tester',
                'email': 'tester@example.com',
                'subject': 'Contact',
                'message': 'Testing contact form'
            })
            assert response.status_code == 302
        finally:
            patch.stopall()
