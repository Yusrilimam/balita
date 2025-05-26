from . import Model
from datetime import datetime

class Pengukuran(Model):
    """Model class untuk data pengukuran"""
    
    TABLE_NAME = 'pengukuran'
    REQUIRED_FIELDS = ['balita_id', 'tanggal_ukur', 'berat_badan', 'tinggi_badan', 'lingkar_lengan']

    @classmethod
    def get_by_id(cls, id):
        """Get pengukuran by ID"""
        query = """
            SELECT p.*, b.nama, b.nik 
            FROM pengukuran p
            JOIN balita b ON p.balita_id = b.id
            WHERE p.id = ?
        """
        return cls.query_db(query, (id,), one=True)

    @classmethod
    def get_by_balita(cls, balita_id, page=1, per_page=10):
        """Get pengukuran by balita ID"""
        query = """
            SELECT p.*, b.nama, b.nik
            FROM pengukuran p
            JOIN balita b ON p.balita_id = b.id
            WHERE p.balita_id = ?
            ORDER BY p.tanggal_ukur DESC
        """
        return cls.paginate(query, (balita_id,), page, per_page)

    @classmethod
    def get_all(cls, page=1, per_page=10, start_date=None, end_date=None):
        """Get all pengukuran with optional date range"""
        query = """
            SELECT p.*, b.nama, b.nik
            FROM pengukuran p
            JOIN balita b ON p.balita_id = b.id
        """
        args = []

        if start_date or end_date:
            conditions = []
            if start_date:
                conditions.append("p.tanggal_ukur >= ?")
                args.append(cls.format_date(start_date))
            if end_date:
                conditions.append("p.tanggal_ukur <= ?")
                args.append(cls.format_date(end_date))
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY p.tanggal_ukur DESC"
        
        return cls.paginate(query, tuple(args), page, per_page)

    @classmethod
    def create(cls, data):
        """Create new pengukuran"""
        # Validate required fields
        errors = cls.validate_required(data, cls.REQUIRED_FIELDS)
        if errors:
            raise ValueError(errors)

        # Format tanggal ukur
        data['tanggal_ukur'] = cls.format_date(data['tanggal_ukur'])
        if not data['tanggal_ukur']:
            raise ValueError(["Invalid date format for tanggal_ukur"])

        # Validate numeric values
        numeric_fields = ['berat_badan', 'tinggi_badan', 'lingkar_lengan']
        for field in numeric_fields:
            try:
                data[field] = float(data[field])
                if data[field] <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError([f"Invalid value for {field}"])

        # Create pengukuran
        return cls.insert_db(cls.TABLE_NAME, data)

    @classmethod
    def update(cls, id, data):
        """Update pengukuran"""
        # Validate required fields
        errors = cls.validate_required(data, cls.REQUIRED_FIELDS)
        if errors:
            raise ValueError(errors)

        # Format tanggal ukur
        data['tanggal_ukur'] = cls.format_date(data['tanggal_ukur'])
        if not data['tanggal_ukur']:
            raise ValueError(["Invalid date format for tanggal_ukur"])

        # Validate numeric values
        numeric_fields = ['berat_badan', 'tinggi_badan', 'lingkar_lengan']
        for field in numeric_fields:
            try:
                data[field] = float(data[field])
                if data[field] <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError([f"Invalid value for {field}"])

        # Update pengukuran
        return cls.update_db(cls.TABLE_NAME, data, {'id': id})

    @classmethod
    def delete(cls, id):
        """Delete pengukuran"""
        return cls.delete_db(cls.TABLE_NAME, {'id': id})

    @classmethod
    def get_statistics(cls, start_date=None, end_date=None):
        """Get pengukuran statistics"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status_gizi = 'normal' THEN 1 ELSE 0 END) as normal,
                SUM(CASE WHEN status_gizi = 'kurang' THEN 1 ELSE 0 END) as kurang,
                SUM(CASE WHEN status_gizi = 'buruk' THEN 1 ELSE 0 END) as buruk,
                AVG(berat_badan) as rata_berat,
                AVG(tinggi_badan) as rata_tinggi,
                AVG(lingkar_lengan) as rata_lila
            FROM pengukuran
        """
        args = []

        if start_date or end_date:
            conditions = []
            if start_date:
                conditions.append("tanggal_ukur >= ?")
                args.append(cls.format_date(start_date))
            if end_date:
                conditions.append("tanggal_ukur <= ?")
                args.append(cls.format_date(end_date))
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        return cls.query_db(query, tuple(args), one=True)

    @classmethod
    def get_trend_data(cls, balita_id):
        """Get trend data for a balita"""
        query = """
            SELECT 
                tanggal_ukur,
                berat_badan,
                tinggi_badan,
                lingkar_lengan,
                status_gizi
            FROM pengukuran
            WHERE balita_id = ?
            ORDER BY tanggal_ukur
        """
        return cls.query_db(query, (balita_id,))