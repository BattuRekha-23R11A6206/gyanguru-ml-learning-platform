"""
User Model for Authentication
"""
import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Simple JSON-based user storage (can be upgraded to SQLite later)
USERS_FILE = 'data/users.json'

def ensure_users_file():
    """Ensure users.json exists"""
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)

def load_users():
    """Load all users from JSON file"""
    ensure_users_file()
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    """Save users to JSON file"""
    ensure_users_file()
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

class User:
    """User model for authentication"""
    
    def __init__(self, username, email, password_hash=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = datetime.now().isoformat()
        self.last_login = None
        self.is_active = True
    
    def set_password(self, password):
        """Hash and set password"""
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary for JSON storage"""
        return {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'is_active': self.is_active
        }
    
    @staticmethod
    def from_dict(data):
        """Create User from dictionary"""
        user = User(data['username'], data['email'], data['password_hash'])
        user.created_at = data.get('created_at', datetime.now().isoformat())
        user.last_login = data.get('last_login')
        user.is_active = data.get('is_active', True)
        return user
    
    @staticmethod
    def create(username, email, password):
        """Create a new user"""
        users = load_users()
        
        # Validate input
        if not username or not email or not password:
            raise ValueError("Username, email, and password are required")
        
        if username in users:
            raise ValueError("Username already exists")
        
        # Check if email exists
        for user_data in users.values():
            if user_data['email'] == email:
                raise ValueError("Email already registered")
        
        # Create new user
        user = User(username, email)
        user.set_password(password)
        
        users[username] = user.to_dict()
        save_users(users)
        
        return user
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        users = load_users()
        if username in users:
            return User.from_dict(users[username])
        return None
    
    @staticmethod
    def authenticate(username, password):
        """Authenticate user and return user if valid"""
        user = User.get_by_username(username)
        if user and user.check_password(password):
            # Update last login
            users = load_users()
            users[username]['last_login'] = datetime.now().isoformat()
            save_users(users)
            return user
        return None
    
    @staticmethod
    def exists(username):
        """Check if user exists"""
        users = load_users()
        return username in users
