from .users import User
from .balita import Balita
from .pengukuran import Pengukuran
from .knn import KNN
from .lvq import LVQ

# Base model class that other models will inherit from
class Model:
    """Base model class with common functionality"""
    
    @classmethod
    def get_db(cls):
        """Get database connection"""
        from app.database import get_db
        return get_db()

    @classmethod
    def query_db(cls, query, args=(), one=False):
        """Execute a database query"""
        from app.database import query_db
        return query_db(query, args, one)

    @classmethod
    def insert_db(cls, table, fields=None):
        """Insert a new record"""
        from app.database import insert_db
        return insert_db(table, fields)

    @classmethod
    def update_db(cls, table, fields=None, condition=None):
        """Update existing record(s)"""
        from app.database import update_db
        return update_db(table, fields, condition)

    @classmethod
    def delete_db(cls, table, condition=None):
        """Delete record(s)"""
        from app.database import delete_db
        return delete_db(table, condition)

    @staticmethod
    def to_dict(row):
        """Convert SQLite Row to dictionary"""
        return dict(zip(row.keys(), row)) if row else None

    @staticmethod
    def format_date(date_str):
        """Format date string to database format"""
        from datetime import datetime
        if isinstance(date_str, str):
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
            except ValueError:
                return None
        return date_str

    @staticmethod
    def format_datetime(datetime_str):
        """Format datetime string to database format"""
        from datetime import datetime
        if isinstance(datetime_str, str):
            try:
                return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                return None
        return datetime_str

    @classmethod
    def paginate(cls, query, args=(), page=1, per_page=10):
        """Paginate query results"""
        offset = (page - 1) * per_page
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM ({query})"
        total = cls.query_db(count_query, args, one=True)['count']
        
        # Get paginated results
        paginated_query = f"{query} LIMIT ? OFFSET ?"
        items = cls.query_db(paginated_query, args + (per_page, offset))
        
        return {
            'items': items,
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }

    @classmethod
    def validate_required(cls, data, fields):
        """Validate required fields"""
        errors = []
        for field in fields:
            if field not in data or not str(data[field]).strip():
                errors.append(f"{field.replace('_', ' ').title()} is required")
        return errors

    @classmethod
    def validate_unique(cls, table, field, value, exclude_id=None):
        """Validate unique field"""
        query = f"SELECT COUNT(*) as count FROM {table} WHERE {field} = ?"
        args = [value]
        
        if exclude_id:
            query += " AND id != ?"
            args.append(exclude_id)
            
        result = cls.query_db(query, tuple(args), one=True)
        return result['count'] == 0

    @classmethod
    def get_by_id(cls, id):
        """Get record by ID"""
        raise NotImplementedError("Subclasses must implement get_by_id()")

    @classmethod
    def get_all(cls):
        """Get all records"""
        raise NotImplementedError("Subclasses must implement get_all()")

    @classmethod
    def create(cls, data):
        """Create a new record"""
        raise NotImplementedError("Subclasses must implement create()")

    @classmethod
    def update(cls, id, data):
        """Update an existing record"""
        raise NotImplementedError("Subclasses must implement update()")

    @classmethod
    def delete(cls, id):
        """Delete a record"""
        raise NotImplementedError("Subclasses must implement delete()")