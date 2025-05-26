from flask import (
    Blueprint, render_template, request, current_app, 
    send_file, flash, redirect, url_for, jsonify
)
from app.models.balita import Balita
from app.models.pengukuran import Pengukuran
from app.utils.decorators import login_required
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import os

bp = Blueprint('laporan', __name__, url_prefix='/laporan')

@bp.route('/')
@login_required
def index():
    """Halaman utama laporan"""
    # Get filter parameters
    start_date = request.args.get('start_date', 
                                (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', 
                              datetime.utcnow().strftime('%Y-%m-%d'))
    jenis_kelamin = request.args.get('jenis_kelamin', '')
    status_gizi = request.args.get('status_gizi', '')
    
    # Get statistics
    stats = get_report_statistics(start_date, end_date, jenis_kelamin, status_gizi)
    
    # Get data for summary table
    summary_data = get_summary_data(start_date, end_date, jenis_kelamin, status_gizi)
    
    return render_template('laporan/index.html',
                         stats=stats,
                         summary_data=summary_data,
                         start_date=start_date,
                         end_date=end_date,
                         jenis_kelamin=jenis_kelamin,
                         status_gizi=status_gizi)

@bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """Generate laporan dalam format yang dipilih"""
    # Get parameters
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    jenis_kelamin = request.form.get('jenis_kelamin')
    status_gizi = request.form.get('status_gizi')
    format_type = request.form.get('format', 'pdf')
    
    try:
        if format_type == 'excel':
            return generate_excel_report(start_date, end_date, jenis_kelamin, status_gizi)
        elif format_type == 'pdf':
            return generate_pdf_report(start_date, end_date, jenis_kelamin, status_gizi)
        else:
            flash('Format laporan tidak valid.', 'danger')
            return redirect(url_for('laporan.index'))
            
    except Exception as e:
        flash('Terjadi kesalahan saat membuat laporan.', 'danger')
        return redirect(url_for('laporan.index'))

def get_report_statistics(start_date, end_date, jenis_kelamin=None, status_gizi=None):
    """Get statistics for report"""
    query = """
        SELECT 
            COUNT(DISTINCT p.balita_id) as total_balita,
            COUNT(p.id) as total_pengukuran,
            SUM(CASE WHEN p.status_gizi = 'normal' THEN 1 ELSE 0 END) as status_normal,
            SUM(CASE WHEN p.status_gizi = 'kurang' THEN 1 ELSE 0 END) as status_kurang,
            SUM(CASE WHEN p.status_gizi = 'buruk' THEN 1 ELSE 0 END) as status_buruk,
            AVG(p.berat_badan) as rata_berat,
            AVG(p.tinggi_badan) as rata_tinggi,
            AVG(p.lingkar_lengan) as rata_lila
        FROM pengukuran p
        JOIN balita b ON p.balita_id = b.id
        WHERE p.tanggal_ukur BETWEEN ? AND ?
    """
    params = [start_date, end_date]
    
    if jenis_kelamin:
        query += " AND b.jenis_kelamin = ?"
        params.append(jenis_kelamin)
    
    if status_gizi:
        query += " AND p.status_gizi = ?"
        params.append(status_gizi)
    
    return Pengukuran.query_db(query, tuple(params), one=True)

def get_summary_data(start_date, end_date, jenis_kelamin=None, status_gizi=None):
    """Get summary data for report"""
    query = """
        SELECT 
            b.nama,
            b.nik,
            b.tanggal_lahir,
            b.jenis_kelamin,
            p.tanggal_ukur,
            p.berat_badan,
            p.tinggi_badan,
            p.lingkar_lengan,
            p.status_gizi
        FROM pengukuran p
        JOIN balita b ON p.balita_id = b.id
        WHERE p.tanggal_ukur BETWEEN ? AND ?
    """
    params = [start_date, end_date]
    
    if jenis_kelamin:
        query += " AND b.jenis_kelamin = ?"
        params.append(jenis_kelamin)
    
    if status_gizi:
        query += " AND p.status_gizi = ?"
        params.append(status_gizi)
    
    query += " ORDER BY p.tanggal_ukur DESC"
    
    return Pengukuran.query_db(query, tuple(params))

def generate_excel_report(start_date, end_date, jenis_kelamin=None, status_gizi=None):
    """Generate Excel report"""
    # Get data
    data = get_summary_data(start_date, end_date, jenis_kelamin, status_gizi)
    stats = get_report_statistics(start_date, end_date, jenis_kelamin, status_gizi)
    
    # Create Excel writer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Create summary sheet
        summary_df = pd.DataFrame([{
            'Periode': f"{start_date} s/d {end_date}",
            'Total Balita': stats['total_balita'],
            'Total Pengukuran': stats['total_pengukuran'],
            'Status Normal': stats['status_normal'],
            'Status Kurang': stats['status_kurang'],
            'Status Buruk': stats['status_buruk'],
            'Rata-rata Berat': f"{stats['rata_berat']:.2f} kg",
            'Rata-rata Tinggi': f"{stats['rata_tinggi']:.2f} cm",
            'Rata-rata LILA': f"{stats['rata_lila']:.2f} cm"
        }])
        summary_df.to_excel(writer, sheet_name='Ringkasan', index=False)
        
        # Create detailed data sheet
        detail_df = pd.DataFrame(data)
        detail_df.to_excel(writer, sheet_name='Data Detail', index=False)
        
        # Get workbook and worksheet objects
        workbook = writer.book
        summary_sheet = writer.sheets['Ringkasan']
        detail_sheet = writer.sheets['Data Detail']
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': '#D3D3D3'
        })
        
        # Apply formats
        for col_num, value in enumerate(summary_df.columns.values):
            summary_sheet.write(0, col_num, value, header_format)
            
        for col_num, value in enumerate(detail_df.columns.values):
            detail_sheet.write(0, col_num, value, header_format)
        
        # Adjust column widths
        for sheet in [summary_sheet, detail_sheet]:
            for column in sheet.dim_colinfo:
                sheet.set_column(column[0], column[0], 15)
    
    # Prepare response
    output.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'laporan_gizi_balita_{timestamp}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

def generate_pdf_report(start_date, end_date, jenis_kelamin=None, status_gizi=None):
    """Generate PDF report"""
    # Get data
    data = get_summary_data(start_date, end_date, jenis_kelamin, status_gizi)
    stats = get_report_statistics(start_date, end_date, jenis_kelamin, status_gizi)
    
    # Create plots
    create_report_plots(data, stats)
    
    # Generate PDF using template
    return render_template('laporan/pdf_report.html',
                         data=data,
                         stats=stats,
                         start_date=start_date,
                         end_date=end_date,
                         jenis_kelamin=jenis_kelamin,
                         status_gizi=status_gizi)

def create_report_plots(data, stats):
    """Create plots for PDF report"""
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Create status distribution pie chart
    plt.figure(figsize=(8, 6))
    status_counts = df['status_gizi'].value_counts()
    plt.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%')
    plt.title('Distribusi Status Gizi')
    plt.savefig('static/temp/status_dist.png')
    plt.close()
    
    # Create gender distribution pie chart
    plt.figure(figsize=(8, 6))
    gender_counts = df['jenis_kelamin'].value_counts()
    plt.pie(gender_counts, labels=['Laki-laki', 'Perempuan'], autopct='%1.1f%%')
    plt.title('Distribusi Jenis Kelamin')
    plt.savefig('static/temp/gender_dist.png')
    plt.close()
    
    # Create measurement trends line plot
    plt.figure(figsize=(12, 6))
    df['tanggal_ukur'] = pd.to_datetime(df['tanggal_ukur'])
    df.sort_values('tanggal_ukur', inplace=True)
    
    plt.plot(df['tanggal_ukur'], df['berat_badan'], label='Berat Badan')
    plt.plot(df['tanggal_ukur'], df['tinggi_badan'], label='Tinggi Badan')
    plt.plot(df['tanggal_ukur'], df['lingkar_lengan'], label='LILA')
    
    plt.title('Tren Pengukuran')
    plt.xlabel('Tanggal')
    plt.ylabel('Nilai')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('static/temp/measurement_trends.png')
    plt.close()

@bp.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def format_date(date_str):
        """Format date string to readable format"""
        if date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%d %B %Y')
        return ''
    
    return dict(format_date=format_date)