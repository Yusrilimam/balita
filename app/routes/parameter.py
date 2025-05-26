from flask import (
    Blueprint, render_template, request, flash, 
    redirect, url_for, jsonify, current_app
)
from app.models.knn import KNN
from app.models.lvq import LVQ
from app.utils.decorators import login_required, admin_required
from datetime import datetime
import numpy as np

bp = Blueprint('parameter', __name__, url_prefix='/parameter')

@bp.route('/')
@login_required
def index():
    """Halaman manajemen parameter"""
    # Get current parameters
    knn_params = KNN.get_parameters()
    
    # Get accuracy history
    knn_accuracy = KNN.get_accuracy_history()
    lvq_performance = LVQ.get_performance_history()
    
    return render_template('parameter/index.html',
                         knn_params=knn_params,
                         knn_accuracy=knn_accuracy,
                         lvq_performance=lvq_performance)

@bp.route('/knn', methods=['POST'])
@admin_required
def update_knn():
    """Update parameter KNN"""
    try:
        # Get form data
        nilai_k = int(request.form['nilai_k'])
        bobot_berat = float(request.form['bobot_berat'])
        bobot_tinggi = float(request.form['bobot_tinggi'])
        bobot_lila = float(request.form['bobot_lila'])
        
        # Validate parameters
        if nilai_k < 1:
            raise ValueError("Nilai K harus lebih besar dari 0")
        
        if any(w < 0 for w in [bobot_berat, bobot_tinggi, bobot_lila]):
            raise ValueError("Bobot tidak boleh negatif")
        
        # Save parameters
        parameter_id = KNN.save_parameters(
            nilai_k, bobot_berat, bobot_tinggi, bobot_lila
        )
        
        # Evaluate model with new parameters
        accuracy = evaluate_knn_model(nilai_k, [bobot_berat, bobot_tinggi, bobot_lila])
        
        # Save accuracy
        KNN.save_accuracy(accuracy, parameter_id)
        
        flash(f'Parameter KNN berhasil diperbarui. Akurasi: {accuracy:.2f}%', 'success')
        
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash('Terjadi kesalahan saat memperbarui parameter.', 'danger')
    
    return redirect(url_for('parameter.index'))

@bp.route('/lvq', methods=['POST'])
@admin_required
def update_lvq():
    """Update parameter LVQ"""
    try:
        # Get form data
        learning_rate = float(request.form['learning_rate'])
        n_epochs = int(request.form['n_epochs'])
        
        # Validate parameters
        if learning_rate <= 0 or learning_rate >= 1:
            raise ValueError("Learning rate harus antara 0 dan 1")
        
        if n_epochs < 1:
            raise ValueError("Jumlah epoch harus lebih besar dari 0")
        
        # Initialize and train LVQ model
        model = LVQ(n_epochs=n_epochs, learning_rate=learning_rate)
        accuracy = evaluate_lvq_model(model)
        
        # Save performance
        LVQ.save_accuracy(accuracy, {
            'learning_rate': learning_rate,
            'n_epochs': n_epochs
        })
        
        flash(f'Parameter LVQ berhasil diperbarui. Akurasi: {accuracy:.2f}%', 'success')
        
    except ValueError as e:
        flash(str(e), 'danger')
    except Exception as e:
        flash('Terjadi kesalahan saat memperbarui parameter.', 'danger')
    
    return redirect(url_for('parameter.index'))

def evaluate_knn_model(k, weights):
    """Evaluate KNN model with given parameters"""
    # Get training data
    query = """
        SELECT 
            p.berat_badan, p.tinggi_badan, p.lingkar_lengan,
            p.status_gizi
        FROM pengukuran p
        WHERE p.status_gizi IS NOT NULL
        ORDER BY p.tanggal_ukur DESC
        LIMIT 1000
    """
    data = KNN.query_db(query)
    
    if not data:
        raise ValueError("Tidak cukup data untuk evaluasi")
    
    # Prepare data
    X = np.array([[d['berat_badan'], d['tinggi_badan'], d['lingkar_lengan']] 
                  for d in data])
    y = np.array([d['status_gizi'] for d in data])
    
    # Split data (70% training, 30% validation)
    split_idx = int(len(X) * 0.7)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    # Evaluate model
    results = KNN.evaluate(X_train, y_train, X_val, y_val, k=k, weights=weights)
    
    return results['accuracy'] * 100

def evaluate_lvq_model(model):
    """Evaluate LVQ model"""
    # Get training data
    query = """
        SELECT 
            p.berat_badan, p.tinggi_badan, p.lingkar_lengan,
            p.status_gizi
        FROM pengukuran p
        WHERE p.status_gizi IS NOT NULL
        ORDER BY p.tanggal_ukur DESC
        LIMIT 1000
    """
    data = LVQ.query_db(query)
    
    if not data:
        raise ValueError("Tidak cukup data untuk evaluasi")
    
    # Prepare data
    X = np.array([[d['berat_badan'], d['tinggi_badan'], d['lingkar_lengan']] 
                  for d in data])
    y = np.array([d['status_gizi'] for d in data])
    
    # Split data (70% training, 30% validation)
    split_idx = int(len(X) * 0.7)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    # Train and evaluate model
    model.fit(X_train, y_train)
    results = model.evaluate(X_val, y_val)
    
    return results['accuracy'] * 100

@bp.route('/chart-data')
@login_required
def get_chart_data():
    """Get data for accuracy charts"""
    # Get KNN accuracy history
    knn_history = KNN.get_accuracy_history()
    
    # Get LVQ performance history
    lvq_history = LVQ.get_performance_history()
    
    # Prepare chart data
    knn_data = {
        'labels': [h['created_at'] for h in knn_history],
        'accuracy': [h['accuracy'] for h in knn_history],
        'parameters': [f"K={h['nilai_k']}" for h in knn_history]
    }
    
    lvq_data = {
        'labels': [h['created_at'] for h in lvq_history],
        'accuracy': [h['accuracy'] for h in lvq_history],
        'parameters': [f"LR={eval(h['parameters'])['learning_rate']}" 
                      for h in lvq_history]
    }
    
    return jsonify({
        'knn': knn_data,
        'lvq': lvq_data
    })

@bp.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def format_datetime(dt_str):
        """Format datetime string"""
        if dt_str:
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d %B %Y %H:%M')
        return ''
    
    return dict(format_datetime=format_datetime)