from flask import (
    Blueprint, flash, redirect, render_template, request, 
    url_for, current_app, jsonify
)
from app.models.balita import Balita
from app.models.pengukuran import Pengukuran
from app.utils.decorators import login_required
from datetime import datetime
import csv
import io

bp = Blueprint('balita', __name__, url_prefix='/balita')

@bp.route('/')
@login_required
def index():
    """Tampilkan daftar balita"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Get balita data with pagination
    balita_data = Balita.get_all(search=search, page=page)
    
    # Get statistics
    stats = Balita.get_statistics()
    
    return render_template('balita/index.html', 
                         balita_data=balita_data, 
                         search=search,
                         stats=stats)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """Tambah data balita baru"""
    if request.method == 'POST':
        try:
            # Get form data
            balita_data = {
                'nik': request.form['nik'],
                'nama': request.form['nama'],
                'tanggal_lahir': request.form['tanggal_lahir'],
                'jenis_kelamin': request.form['jenis_kelamin'],
                'nama_ortu': request.form['nama_ortu'],
                'alamat': request.form.get('alamat', '')
            }
            
            # Create new balita
            balita_id = Balita.create(balita_data)
            
            flash('Data balita berhasil ditambahkan.', 'success')
            return redirect(url_for('balita.detail', id=balita_id))
            
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('Terjadi kesalahan saat menambahkan data balita.', 'danger')
    
    return render_template('balita/create.html')

@bp.route('/<int:id>')
@login_required
def detail(id):
    """Tampilkan detail balita"""
    balita = Balita.get_by_id(id)
    if balita is None:
        flash('Data balita tidak ditemukan.', 'danger')
        return redirect(url_for('balita.index'))
    
    # Get pengukuran history
    page = request.args.get('page', 1, type=int)
    pengukuran_data = Pengukuran.get_by_balita(id, page=page)
    
    # Get trend data for charts
    trend_data = Pengukuran.get_trend_data(id)
    
    return render_template('balita/detail.html',
                         balita=balita,
                         pengukuran_data=pengukuran_data,
                         trend_data=trend_data)

@bp.route('/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
    """Edit data balita"""
    balita = Balita.get_by_id(id)
    if balita is None:
        flash('Data balita tidak ditemukan.', 'danger')
        return redirect(url_for('balita.index'))
    
    if request.method == 'POST':
        try:
            # Get form data
            balita_data = {
                'nik': request.form['nik'],
                'nama': request.form['nama'],
                'tanggal_lahir': request.form['tanggal_lahir'],
                'jenis_kelamin': request.form['jenis_kelamin'],
                'nama_ortu': request.form['nama_ortu'],
                'alamat': request.form.get('alamat', '')
            }
            
            # Update balita
            if Balita.update(id, balita_data):
                flash('Data balita berhasil diperbarui.', 'success')
                return redirect(url_for('balita.detail', id=id))
            
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('Terjadi kesalahan saat memperbarui data balita.', 'danger')
    
    return render_template('balita/edit.html', balita=balita)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    """Hapus data balita"""
    try:
        if Balita.delete(id):
            flash('Data balita berhasil dihapus.', 'success')
        else:
            flash('Gagal menghapus data balita.', 'danger')
    except Exception as e:
        flash('Terjadi kesalahan saat menghapus data balita.', 'danger')
    
    return redirect(url_for('balita.index'))

@bp.route('/export')
@login_required
def export():
    """Export data balita ke CSV"""
    try:
        # Get all balita data
        balita_data = Balita.get_all(per_page=1000)['items']
        
        # Create CSV file in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['NIK', 'Nama', 'Tanggal Lahir', 'Jenis Kelamin', 
                        'Nama Orang Tua', 'Alamat', 'Jumlah Pengukuran',
                        'Pengukuran Terakhir'])
        
        # Write data
        for balita in balita_data:
            writer.writerow([
                balita['nik'],
                balita['nama'],
                balita['tanggal_lahir'],
                balita['jenis_kelamin'],
                balita['nama_ortu'],
                balita['alamat'],
                balita['jumlah_pengukuran'],
                balita['pengukuran_terakhir']
            ])
        
        # Prepare response
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return current_app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=data_balita_{timestamp}.csv'
            }
        )
        
    except Exception as e:
        flash('Terjadi kesalahan saat mengexport data.', 'danger')
        return redirect(url_for('balita.index'))

@bp.route('/check_nik')
@login_required
def check_nik():
    """Check if NIK is already registered"""
    nik = request.args.get('nik', '')
    balita_id = request.args.get('id', None, type=int)
    
    if not nik:
        return jsonify({'valid': False, 'message': 'NIK is required'})
    
    # Check NIK format (16 digits)
    if not nik.isdigit() or len(nik) != 16:
        return jsonify({'valid': False, 'message': 'NIK harus 16 digit angka'})
    
    # Check NIK uniqueness
    existing = Balita.get_by_nik(nik)
    if existing and (not balita_id or existing['id'] != balita_id):
        return jsonify({'valid': False, 'message': 'NIK sudah terdaftar'})
    
    return jsonify({'valid': True})

@bp.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def calculate_age(birth_date):
        """Calculate age in years and months"""
        if not birth_date:
            return ''
        
        birth = datetime.strptime(birth_date, '%Y-%m-%d')
        today = datetime.utcnow()
        
        years = today.year - birth.year
        months = today.month - birth.month
        
        if today.day < birth.day:
            months -= 1
        
        if months < 0:
            years -= 1
            months += 12
            
        if years == 0:
            return f"{months} bulan"
        return f"{years} tahun {months} bulan"
    
    return dict(calculate_age=calculate_age)