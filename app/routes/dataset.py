from flask import (
    Blueprint, render_template, request, flash, 
    redirect, url_for, current_app, send_file
)
from app.models.pengukuran import Pengukuran
from app.models.balita import Balita
from app.models.knn import KNN
from app.models.lvq import LVQ
from app.utils.decorators import login_required, admin_required
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
from datetime import datetime
import os
import csv
import io

bp = Blueprint('dataset', __name__, url_prefix='/dataset')

@bp.route('/')
@login_required
def index():
    """Halaman manajemen dataset"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Get dataset with pagination
    dataset = Pengukuran.get_all(
        page=page,
        per_page=20,
        search=search
    )
    
    # Get statistics
    stats = {
        'total_data': dataset['total'],
        'labeled_data': count_labeled_data(),
        'unlabeled_data': count_unlabeled_data()
    }
    
    return render_template('dataset/index.html',
                         dataset=dataset,
                         stats=stats,
                         search=search)

@bp.route('/upload', methods=['POST'])
@admin_required
def upload():
    """Upload dataset dari file CSV"""
    if 'dataset' not in request.files:
        flash('Tidak ada file yang dipilih.', 'danger')
        return redirect(url_for('dataset.index'))
    
    file = request.files['dataset']
    if file.filename == '':
        flash('Tidak ada file yang dipilih.', 'danger')
        return redirect(url_for('dataset.index'))
    
    if not file.filename.endswith('.csv'):
        flash('File harus berformat CSV.', 'danger')
        return redirect(url_for('dataset.index'))
    
    try:
        # Read CSV file
        df = pd.read_csv(file)
        
        # Validate columns
        required_columns = ['nik', 'tanggal_ukur', 'berat_badan', 
                          'tinggi_badan', 'lingkar_lengan']
        
        if not all(col in df.columns for col in required_columns):
            flash('Format CSV tidak sesuai.', 'danger')
            return redirect(url_for('dataset.index'))
        
        # Process each row
        success_count = 0
        error_count = 0
        
        for _, row in df.iterrows():
            try:
                # Get balita by NIK
                balita = Balita.get_by_nik(str(row['nik']))
                if not balita:
                    error_count += 1
                    continue
                
                # Prepare pengukuran data
                pengukuran_data = {
                    'balita_id': balita['id'],
                    'tanggal_ukur': row['tanggal_ukur'],
                    'berat_badan': float(row['berat_badan']),
                    'tinggi_badan': float(row['tinggi_badan']),
                    'lingkar_lengan': float(row['lingkar_lengan']),
                    'status_gizi': row.get('status_gizi')
                }
                
                # Create pengukuran
                Pengukuran.create(pengukuran_data)
                success_count += 1
                
            except Exception:
                error_count += 1
        
        flash(f'Import selesai. Berhasil: {success_count}, Gagal: {error_count}', 
              'success' if error_count == 0 else 'warning')
        
    except Exception as e:
        flash('Terjadi kesalahan saat memproses file.', 'danger')
    
    return redirect(url_for('dataset.index'))

@bp.route('/export')
@login_required
def export():
    """Export dataset ke CSV"""
    try:
        # Get all data
        query = """
            SELECT 
                b.nik,
                b.nama,
                b.tanggal_lahir,
                b.jenis_kelamin,
                p.tanggal_ukur,
                p.berat_badan,
                p.tinggi_badan,
                p.lingkar_lengan,
                p.status_gizi
            FROM pengukuran p
            JOIN balita b ON p.balita_id = b.id
            ORDER BY p.tanggal_ukur DESC
        """
        data = Pengukuran.query_db(query)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'NIK', 'Nama', 'Tanggal Lahir', 'Jenis Kelamin',
            'Tanggal Ukur', 'Berat Badan', 'Tinggi Badan',
            'Lingkar Lengan', 'Status Gizi'
        ])
        
        # Write data
        for row in data:
            writer.writerow([
                row['nik'],
                row['nama'],
                row['tanggal_lahir'],
                row['jenis_kelamin'],
                row['tanggal_ukur'],
                row['berat_badan'],
                row['tinggi_badan'],
                row['lingkar_lengan'],
                row['status_gizi']
            ])
        
        # Prepare response
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'dataset_pengukuran_{timestamp}.csv'
        )
        
    except Exception as e:
        flash('Terjadi kesalahan saat mengexport data.', 'danger')
        return redirect(url_for('dataset.index'))

@bp.route('/predict', methods=['POST'])
@login_required
def predict():
    """Prediksi status gizi menggunakan model"""
    try:
        # Get form data
        berat = float(request.form['berat_badan'])
        tinggi = float(request.form['tinggi_badan'])
        lila = float(request.form['lingkar_lengan'])
        model_type = request.form['model']
        
        # Prepare input data
        X = np.array([[berat, tinggi, lila]])
        
        # Get prediction
        if model_type == 'knn':
            # Get current KNN parameters
            params = KNN.get_parameters()
            if not params:
                raise ValueError("Parameter KNN belum diatur")
            
            # Predict using KNN
            prediction = KNN.predict(
                X_train=get_training_data(),
                y_train=get_training_labels(),
                X_test=X,
                k=params['nilai_k'],
                weights=[params['bobot_berat'], 
                        params['bobot_tinggi'], 
                        params['bobot_lila']]
            )
        else:
            # Initialize LVQ model
            model = LVQ()
            X_train, y_train = get_training_data(), get_training_labels()
            
            # Train and predict
            model.fit(X_train, y_train)
            prediction = model.predict(X)
        
        return jsonify({
            'status': 'success',
            'prediction': prediction[0]
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Terjadi kesalahan saat melakukan prediksi.'
        }), 500

def count_labeled_data():
    """Count data with status_gizi label"""
    query = "SELECT COUNT(*) as count FROM pengukuran WHERE status_gizi IS NOT NULL"
    result = Pengukuran.query_db(query, one=True)
    return result['count']

def count_unlabeled_data():
    """Count data without status_gizi label"""
    query = "SELECT COUNT(*) as count FROM pengukuran WHERE status_gizi IS NULL"
    result = Pengukuran.query_db(query, one=True)
    return result['count']

def get_training_data():
    """Get features for training"""
    query = """
        SELECT berat_badan, tinggi_badan, lingkar_lengan
        FROM pengukuran
        WHERE status_gizi IS NOT NULL
        ORDER BY tanggal_ukur DESC
        LIMIT 1000
    """
    data = Pengukuran.query_db(query)
    return np.array([[d['berat_badan'], d['tinggi_badan'], d['lingkar_lengan']] 
                    for d in data])

def get_training_labels():
    """Get labels for training"""
    query = """
        SELECT status_gizi
        FROM pengukuran
        WHERE status_gizi IS NOT NULL
        ORDER BY tanggal_ukur DESC
        LIMIT 1000
    """
    data = Pengukuran.query_db(query)
    return np.array([d['status_gizi'] for d in data])

@bp.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def format_status(status):
        """Format status gizi"""
        if not status:
            return 'Belum ada status'
        return status.title()
    
    return dict(format_status=format_status)