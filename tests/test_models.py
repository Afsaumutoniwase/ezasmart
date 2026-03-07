"""
Tests for database models
"""
import pytest
from datetime import datetime, timedelta
from app import User, Post, Reply, Category, db


class TestUserModel:
    """Tests for the User model"""
    
    def test_create_user(self, app):
        """Test creating a new user"""
        with app.app_context():
            user = User(
                username='newuser',
                email='newuser@example.com',
                role='farmer',
                gender='female',
                address='456 New Street',
                phone='9876543210'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            saved_user = User.query.filter_by(email='newuser@example.com').first()
            assert saved_user is not None
            assert saved_user.username == 'newuser'
            assert saved_user.email == 'newuser@example.com'
            assert saved_user.role == 'farmer'
    
    def test_password_hashing(self, app):
        """Test that passwords are properly hashed"""
        with app.app_context():
            user = User(username='hashtest', email='hash@example.com')
            user.set_password('mypassword')
            
            assert user.password_hash != 'mypassword'
            assert user.check_password('mypassword') is True
            assert user.check_password('wrongpassword') is False
    
    def test_unique_username(self, app):
        """Test that usernames must be unique"""
        with app.app_context():
            user1 = User(username='duplicate', email='user1@example.com')
            user1.set_password('pass123')
            db.session.add(user1)
            db.session.commit()
            
            user2 = User(username='duplicate', email='user2@example.com')
            user2.set_password('pass456')
            db.session.add(user2)
            
            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()
    
    def test_unique_email(self, app):
        """Test that emails must be unique"""
        with app.app_context():
            user1 = User(username='user1', email='same@example.com')
            user1.set_password('pass123')
            db.session.add(user1)
            db.session.commit()
            
            user2 = User(username='user2', email='same@example.com')
            user2.set_password('pass456')
            db.session.add(user2)
            
            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()
    
    def test_generate_reset_token(self, app, test_user):
        """Test password reset token generation"""
        with app.app_context():
            user = User.query.get(test_user.id)
            token = user.generate_reset_token()
            
            assert token is not None
            assert user.reset_token == token
            assert user.reset_token_expiration is not None
            assert user.reset_token_expiration > datetime.utcnow()
    
    def test_verify_reset_token(self, app, test_user):
        """Test password reset token verification"""
        with app.app_context():
            user = User.query.get(test_user.id)
            token = user.generate_reset_token()
            
            assert user.verify_reset_token(token) is True
            
            assert user.verify_reset_token('invalid_token') is False
    
    def test_expired_reset_token(self, app, test_user):
        """Test that expired tokens are rejected"""
        with app.app_context():
            user = User.query.get(test_user.id)
            token = user.generate_reset_token()
            
            user.reset_token_expiration = datetime.utcnow() - timedelta(hours=2)
            db.session.commit()
            
            assert user.verify_reset_token(token) is False
    
    def test_clear_reset_token(self, app, test_user):
        """Test clearing reset token"""
        with app.app_context():
            user = User.query.get(test_user.id)
            user.generate_reset_token()
            
            assert user.reset_token is not None
            
            user.clear_reset_token()
            
            assert user.reset_token is None
            assert user.reset_token_expiration is None


class TestCategoryModel:
    """Tests for the Category model"""
    
    def test_create_category(self, app):
        """Test creating a new category"""
        with app.app_context():
            category = Category(
                name='Test Category',
                description='A test category description'
            )
            db.session.add(category)
            db.session.commit()
            
            saved_category = Category.query.filter_by(name='Test Category').first()
            assert saved_category is not None
            assert saved_category.name == 'Test Category'
            assert saved_category.description == 'A test category description'
    
    def test_category_repr(self, app):
        """Test category string representation"""
        with app.app_context():
            category = Category(name='Repr Test')
            assert repr(category) == '<Category Repr Test>'


class TestPostModel:
    """Tests for the Post model"""
    
    def test_create_post(self, app, test_user, test_categories):
        """Test creating a new post"""
        with app.app_context():
            user = User.query.get(test_user.id)
            category_id = test_categories[0]
            
            post = Post(
                title='New Test Post',
                content='This is the post content.',
                user_id=user.id,
                category_id=category_id
            )
            db.session.add(post)
            db.session.commit()
            
            saved_post = Post.query.filter_by(title='New Test Post').first()
            assert saved_post is not None
            assert saved_post.content == 'This is the post content.'
            assert saved_post.user_id == user.id
    
    def test_post_user_relationship(self, app, test_user, test_post):
        """Test post-user relationship"""
        with app.app_context():
            post = Post.query.get(test_post)
            user = User.query.get(test_user.id)
            
            assert post.user.id == user.id
            assert post in user.posts
    
    def test_post_category_relationship(self, app, test_post, test_categories):
        """Test post-category relationship"""
        with app.app_context():
            post = Post.query.get(test_post)
            category = Category.query.get(test_categories[0])
            
            assert post.category.id == category.id
            assert post in category.posts
    
    def test_post_created_at(self, app, test_post):
        """Test that posts have a created_at timestamp"""
        with app.app_context():
            post = Post.query.get(test_post)
            assert post.created_at is not None
            assert isinstance(post.created_at, datetime)


class TestReplyModel:
    """Tests for the Reply model"""
    
    def test_create_reply(self, app, test_user, test_post):
        """Test creating a new reply"""
        with app.app_context():
            user = User.query.get(test_user.id)
            
            reply = Reply(
                content='New test reply',
                user_id=user.id,
                post_id=test_post
            )
            db.session.add(reply)
            db.session.commit()
            
            saved_reply = Reply.query.filter_by(content='New test reply').first()
            assert saved_reply is not None
            assert saved_reply.user_id == user.id
            assert saved_reply.post_id == test_post
    
    def test_reply_user_relationship(self, app, test_user, test_reply):
        """Test reply-user relationship"""
        with app.app_context():
            reply = Reply.query.get(test_reply)
            user = User.query.get(test_user.id)
            
            assert reply.user.id == user.id
            assert reply in user.replies
    
    def test_reply_post_relationship(self, app, test_post, test_reply):
        """Test reply-post relationship"""
        with app.app_context():
            reply = Reply.query.get(test_reply)
            post = Post.query.get(test_post)
            
            assert reply.post.id == post.id
            assert reply in post.replies
    
    def test_reply_cascade_delete(self, app, test_post, test_reply):
        """Test that replies are deleted when post is deleted"""
        with app.app_context():
            post = Post.query.get(test_post)
            reply_id = test_reply
            
            reply = Reply.query.get(reply_id)
            assert reply is not None
            
            db.session.delete(post)
            db.session.commit()
            
            reply = Reply.query.get(reply_id)
            assert reply is None
