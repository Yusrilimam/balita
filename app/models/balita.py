from . import Model
from datetime import datetime
from werkzeug.security import generate_password_hash

class Balita(Model):
    """Model class untuk data balita"""
    
    TABLE_NAME = 'balita'
    REQUIRED_FIELDS = ['nik', 'nama', 'tanggal_lahir', 'jenis_kelamin', 'nama_ortu']

    @classmethod
    def get_by_id(cls, id):
        """Get balita by ID"""
        query = """
            SELECT b.*, 
                   COUNT(p.id) as jumlah_pengukuran,
                   MAX(p.tanggal_ukur) as pengukuran_terakhir
            FROM balita b
            LEFT JOIN pengukuran p ON b.id = p.balita_id
            WHERE b.id = ?
            GROUP BY b.id
        """
        return cls.query_db(query, (id,), one=True)

    @classmethod
    def get_by_nik(cls, nik):
        """Get balita by NIK"""
        query = "SELECT * FROM balita WHERE nik = ?"
        return cls.query_db(query, (nik,), one=True)

    @classmethod
    def get_all(cls, search=None, page=1, per_page=10):
        """Get all balita with optional search"""
        query = """
            SELECT b.*, 
                   COUNT(p.id) as jumlah_pengukuran,
                   MAX(p.tanggal_ukur) as pengukuran_terakhir
            FROM balita b
            LEFT JOIN pengukuran p ON b.id = p.balita_id
        """
        args = []

        if search:
            query += """ 
                WHERE b.nama LIKE ? OR b.nik LIKE ? 
                OR b.nama_ortu LIKE ? OR b.alamat LIKE ?
            """
            search_term = f"%{search}%"
            args.extend([search_term] * 4)

        query += " GROUP BY b.id ORDER BY b.nama"
        
        return cls.paginate(query, tuple(args), page, per_page)

    @classmethod
    def create(cls, data):
        """Create new balita"""
        # Validate required fields
        errors = cls.validate_required(data, cls.REQUIRED_FIELDS)
        if errors:
            raise ValueError(errors)

        # Validate unique NIK
        if not cls.validate_unique(cls.TABLE_NAME, 'nik', data['nik']):
            raise ValueError(["NIK already exists"])

        # Format tanggal lahir
        data['tanggal_lahir'] = cls.format_date(data['tanggal_lahir'])
        if not data['tanggal_lahir']:
            raise ValueError(["Invalid date format for tanggal_lahir"])

        # Create balita
        return cls.insert_db(cls.TABLE_NAME, data)

    @classmethod
    def update(cls, id, data):
        """Update balita"""
        # Validate required fields
        errors = cls.validate_required(data, cls.REQUIRED_FIELDS)
        if errors:
            raise ValueError(errors)

        # Validate unique NIK
        if not cls.validate_unique(cls.TABLE_NAME, 'nik', data['nik'], id):
            raise ValueError(["NIK already exists"])

        # Format tanggal lahir
        data['tanggal_lahir'] = cls.format_date(data['tanggal_lahir'])
        if not data['tanggal_lahir']:
            raise ValueError(["Invalid date format for tanggal_lahir"])

        # Update timestamp
        data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Update balita
        return cls.update_db(cls.TABLE_NAME, data, {'id': id})

    @classmethod
    def delete(cls, id):
        """Delete balita and all related pengukuran"""
        db = cls.get_db()
        try:
            # Begin transaction
            db.execute('BEGIN')
            
            # Delete related pengukuran
            db.execute('DELETE FROM pengukuran WHERE balita_id = ?', (id,))
            
            # Delete balita
            db.execute('DELETE FROM balita WHERE id = ?', (id,))
            
            # Commit transaction
            db.commit()
            return True
        except:
            db.rollback()
            raise

    @classmethod
    def get_statistics(cls):
        """Get balita statistics"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN jenis_kelamin = 'L' THEN 1 ELSE 0 END) as laki_laki,
                SUM(CASE WHEN jenis_kelamin = 'P' THEN 1 ELSE 0 END) as perempuan,
                COUNT(DISTINCT p.balita_id) as sudah_diukur
            FROM balita b
            LEFT JOIN pengukuran p ON b.id = p.balita_id
        """
        return cls.query_db(query, one=True)