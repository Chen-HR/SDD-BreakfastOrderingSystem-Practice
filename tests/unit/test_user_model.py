import pytest
from app.models import User
from app import db

def test_password_hashing(app):
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()

        # Test if password was hashed
        assert user.password_hash is not None
        assert user.password_hash != 'testpassword'

        # Test correct password
        assert user.check_password('testpassword')

        # Test incorrect password
        assert not user.check_password('wrongpassword')

def test_password_salt_is_random(app):
    with app.app_context():
        user1 = User(username='user1', email='user1@example.com')
        user1.set_password('testpassword')
        db.session.add(user1)
        db.session.commit()

        user2 = User(username='user2', email='user2@example.com')
        user2.set_password('testpassword')
        db.session.add(user2)
        db.session.commit()

        # Even with the same password, the hashes should be different due to salting
        assert user1.password_hash != user2.password_hash