from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..database import get_db
from ..utils.decorators import login_required
from ..models.pengukuran import Pengukuran
from datetime import datetime

bp = Blueprint('pengukuran', __name__, url_prefix='/pengukuran')

@bp.route('/')
@login_required
def index():
    """Endpoint untuk melihat data pengukuran dengan filter dan pagination"""
    nama_balita = request.args.get('nama_balita', '').strip()
    status_gizi = request.args.get('status_gizi', '').strip()
    page = request.args.get('page', 1, type=int)
    
    pengukuran = Pengukuran.get_all(
        page=page,
        nama_balita=nama_balita,
        status_gizi=status_gizi
    )
    
    return render_template('pengukuran/data.html', pengukuran=pengukuran, page=page)

@bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah():
    if request.method == 'POST':
        balita_id = request.form.get('balita_id', '')
        berat_badan = request.form.get('berat_badan', '')
        tinggi_badan = request.form.get('tinggi_badan', '')
        lingkar_lengan = request.form.get('lingkar_lengan', '')

        if not all([balita_id, berat_badan, tinggi_badan, lingkar_lengan]):
            flash('Semua field harus diisi', 'danger')
            return redirect(url_for('pengukuran.tambah'))

        try:
            pengukuran = Pengukuran(
                balita_id=balita_id,
                tanggal_ukur=datetime.now().date(),
                berat_badan=float(berat_badan),
                tinggi_badan=float(tinggi_badan),
                lingkar_lengan=float(lingkar_lengan)
            )
            pengukuran.save()
            flash('Pengukuran berhasil disimpan', 'success')
            return redirect(url_for('pengukuran.index'))
        except ValueError:
            flash('Input tidak valid. Pastikan angka yang dimasukkan benar', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    # Get list of balita for dropdown
    conn = get_db()
    balita = conn.execute('SELECT id, nama FROM balita ORDER BY nama').fetchall()
    return render_template('pengukuran/tambah.html', balita=balita)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    conn = get_db()
    pengukuran = conn.execute('''
        SELECT p.*, b.nama, b.tanggal_lahir, b.jenis_kelamin
        FROM pengukuran p
        JOIN balita b ON p.balita_id = b.id
        WHERE p.id = ?
    ''', (id,)).fetchone()
    
    if not pengukuran:
        flash('Data pengukuran tidak ditemukan', 'danger')
        return redirect(url_for('pengukuran.index'))

    if request.method == 'POST':
        berat_badan = request.form.get('berat_badan', '')
        tinggi_badan = request.form.get('tinggi_badan', '')
        lingkar_lengan = request.form.get('lingkar_lengan', '')

        try:
            pengukuran_obj = Pengukuran(
                id=id,
                balita_id=pengukuran['balita_id'],
                tanggal_ukur=pengukuran['tanggal_ukur'],
                berat_badan=float(berat_badan),
                tinggi_badan=float(tinggi_badan),
                lingkar_lengan=float(lingkar_lengan)
            )
            pengukuran_obj.save()
            flash('Data pengukuran berhasil diupdate', 'success')
            return redirect(url_for('pengukuran.index'))
        except ValueError:
            flash('Input tidak valid. Pastikan angka yang dimasukkan benar', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            
    return render_template('pengukuran/edit.html', pengukuran=pengukuran)

@bp.route('/hapus/<int:id>')
@login_required
def hapus(id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM pengukuran WHERE id = ?', (id,))
        conn.commit()
        flash('Data pengukuran berhasil dihapus', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('pengukuran.index'))