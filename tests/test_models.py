from src.models import User

def test_password_hashing():
    u = User(email='test@example.com', role='customer')
    u.set_password('mysecretpassword')
    assert u.password_hash is not None
    assert u.password_hash != 'mysecretpassword'

def test_password_checking():
    u = User(email='test2@example.com', role='customer')
    u.set_password('supersecret')
    assert u.check_password('supersecret') is True
    assert u.check_password('anotherpassword') is False
