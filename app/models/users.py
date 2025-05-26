from . import Model
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(Model, UserMixin):
    """Model class untuk user"""
    
    TABLE_NAME = 'users'
    REQUIRED_FIELDS = ['username', 'password', 'nama_lengkap']
    ALLOWED_ROLES = ['admin', 'user']

    def __init__(self, user_data):
        """Initialize user object"""
        self.id = user_data['id']
        self.username = user_data['username']
        self.password = user_data['password']
        self.nama_lengkap = user_data['nama_lengkap']
        self.role = user_data['role']
        self.email = user_data.get('email')
        self.photo = user_data.get('photo')
        self.created_at = user_data.get('created_at')

    @classmethod
    def get_by_id(cls, id):
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = ?"
        user_data = cls.query_db(query, (id,), one=True)
        return cls(user_data) if user_data else None

    @classmethod
    def get_by_username(cls, username):
        """Get user by username"""
        query = "SELECT * FROM users WHERE username = ?"
        user_data = cls.query_db(query, (username,), one=True)
        return cls(user_data) if user_data else None

    @classmethod
    def get_all(cls, search=None, page=1, per_page=10):
        """Get all users with optional search"""
        query = "SELECT * FROM users"
        args = []

        if search:
            query += """ 
                WHERE username LIKE ? 
                OR nama_lengkap LIKE ? 
                OR email LIKE ?
            """
            search_term = f"%{search}%"
            args.extend([search_term] * 3)

        query += " ORDER BY nama_lengkap"
        
        return cls.paginate(query, tuple(args), page, per_page)

    @classmethod
    def create(cls, data):
        """Create new user"""
        # Validate required fields
        errors = cls.validate_required(data, cls.REQUIRED_FIELDS)
        if errors:
            raise ValueError(errors)

        # Validate unique username
        if not cls.validate_unique(cls.TABLE_NAME, 'username', data['username']):
            raise ValueError(["Username already exists"])

        # Validate role
        role = data.get('role', 'user')
        if role not in cls.ALLOWED_ROLES:
            raise ValueError(["Invalid role"])

        # Hash password
        user_data = {
            'username': data['username'],
            'password': generate_password_hash(data['password']),
            'nama_lengkap': data['nama_lengkap'],
            'role': role,
            'email': data.get('email'),
            'photo': data.get('photo'),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Create user
        return cls.insert_db(cls.TABLE_NAME, user_data)

    @classmethod
    def update(cls, id, data):
        """Update user"""
        # Get current user data
        current_user = cls.get_by_id(id)
        if not current_user:
            raise ValueError(["User not found"])

        # Prepare update data
        update_data = {}

        # Update username if provided and changed
        if 'username' in data and data['username'] != current_user.username:
            if not cls.validate_unique(cls.TABLE_NAME, 'username', data['username'], id):
                raise ValueError(["Username already exists"])
            update_data['username'] = data['username']

        # Update password if provided
        if 'password' in data and data['password']:
            update_data['password'] = generate_password_hash(data['password'])

        # Update other fields
        for field in ['nama_lengkap', 'email', 'photo', 'role']:
            if field in data:
                if field == 'role' and data[field] not in cls.ALLOWED_ROLES:
                    raise ValueError(["Invalid role"])
                update_data[field] = data[field]

        if not update_data:
            return False

        # Update user
        return cls.update_db(cls.TABLE_NAME, update_data, {'id': id})

    @classmethod
    def delete(cls, id):
        """Delete user"""
        # Prevent deleting the last admin
        if cls.is_last_admin(id):
            raise ValueError(["Cannot delete the last admin user"])

        return cls.delete_db(cls.TABLE_NAME, {'id': id})

    @classmethod
    def authenticate(cls, username, password):
        """Authenticate user"""
        user = cls.get_by_username(username)
        if user and check_password_hash(user.password, password):
            return user
        return None

    @classmethod
    def change_password(cls, id, current_password, new_password):
        """Change user password"""
        user = cls.get_by_id(id)
        if not user:
            raise ValueError(["User not found"])

        if not check_password_hash(user.password, current_password):
            raise ValueError(["Current password is incorrect"])

        update_data = {
            'password': generate_password_hash(new_password)
        }

        return cls.update_db(cls.TABLE_NAME, update_data, {'id': id})

    @classmethod
    def is_last_admin(cls, user_id):
        """Check if user is the last admin"""
        query = """
            SELECT COUNT(*) as count 
            FROM users 
            WHERE role = 'admin' AND id != ?
        """
        result = cls.query_db(query, (user_id,), one=True)
        return result['count'] == 0

    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'

    def get_id(self):
        """Return user ID for Flask-Login"""
        return str(self.id)

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'nama_lengkap': self.nama_lengkap,
            'role': self.role,
            'email': self.email,
            'photo': self.photo,
            'created_at': self.created_at
        }