"""
Test configuration and fixtures for pytest
"""
import os
import sys
import tempfile
import pytest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app, db, User, Category, Post, Reply


@pytest.fixture(scope='function')
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_path = tempfile.mkstemp()
    
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'MAIL_SUPPRESS_SEND': True,  # Don't send real emails during tests
        'LOGIN_DISABLED': False,
    })
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        
        db.session.remove()
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            role='farmer',
            gender='male',
            address='123 Test Street',
            phone='1234567890',
            profile_image_url='default-profile.png',
            profile_complete=True
        )
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()
        
        user_id = user.id
        
    with app.app_context():
        return User.query.get(user_id)


@pytest.fixture(scope='function')
def authenticated_client(client, test_user, app):
    """A test client with an authenticated user."""
    with app.app_context():
        with client:
            client.post('/login', data={
                'form_type': 'login',
                'email': 'test@example.com',
                'password': 'testpassword123'
            }, follow_redirects=True)
            yield client


@pytest.fixture(scope='function')
def test_categories(app):
    """Create test categories."""
    with app.app_context():
        categories = [
            Category(name='General Discussion', description='General topics'),
            Category(name='Hydroponics 101', description='Beginner topics'),
            Category(name='Advanced Techniques', description='Advanced topics'),
        ]
        db.session.add_all(categories)
        db.session.commit()
        
        category_ids = [cat.id for cat in categories]
        
    return category_ids


@pytest.fixture(scope='function')
def test_post(app, test_user, test_categories):
    """Create a test post."""
    with app.app_context():
        user = User.query.get(test_user.id)
        category_id = test_categories[0]
        
        post = Post(
            title='Test Post',
            content='This is a test post content.',
            user_id=user.id,
            category_id=category_id,
            created_at=datetime.utcnow()
        )
        db.session.add(post)
        db.session.commit()
        
        post_id = post.id
        
    return post_id


@pytest.fixture(scope='function')
def test_reply(app, test_user, test_post):
    """Create a test reply."""
    with app.app_context():
        user = User.query.get(test_user.id)
        
        reply = Reply(
            content='This is a test reply.',
            user_id=user.id,
            post_id=test_post,
            created_at=datetime.utcnow()
        )
        db.session.add(reply)
        db.session.commit()
        
        reply_id = reply.id
        
    return reply_id
