from flask import Blueprint, render_template, g, request
from app.models.balita import Balita
from app.models.pengukuran import Pengukuran
from app.utils.decorators import login_required
from datetime import datetime, timedelta
import json

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    """Halaman dashboard utama"""
    # Get current date and last 30 days
    today = datetime.utcnow()
    last_30_days = today - timedelta(days=30)
    
    # Get statistics
    balita_stats = Balita.get_statistics()
    pengukuran_stats = Pengukuran.get_statistics(
        start_date=last_30_days.strftime('%Y-%m-%d'),
        end_date=today.strftime('%Y-%m-%d')
    )
    
    # Get recent pengukuran
    recent_pengukuran = Pengukuran.get_all(page=1, per_page=5)['items']
    
    # Prepare chart data
    chart_data = prepare_chart_data()
    
    return render_template('dashboard/index.html',
                         balita_stats=balita_stats,
                         pengukuran_stats=pengukuran_stats,
                         recent_pengukuran=recent_pengukuran,
                         chart_data=chart_data)

def prepare_chart_data():
    """Prepare data for dashboard charts"""
    # Get current date and last 6 months
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=180)  # ~6 months
    
    # Initialize data structure
    months = []
    status_data = {
        'normal': [],
        'kurang': [],
        'buruk': []
    }
    
    # Get monthly statistics
    current = start_date
    while current <= end_date:
        month_start = current.replace(day=1)
        if current.month == 12:
            month_end = current.replace(year=current.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = current.replace(month=current.month + 1, day=1) - timedelta(days=1)
        
        # Get statistics for this month
        stats = Pengukuran.get_statistics(
            start_date=month_start.strftime('%Y-%m-%d'),
            end_date=month_end.strftime('%Y-%m-%d')
        )
        
        # Add to data structure
        months.append(current.strftime('%b %Y'))
        status_data['normal'].append(stats['normal'] or 0)
        status_data['kurang'].append(stats['kurang'] or 0)
        status_data['buruk'].append(stats['buruk'] or 0)
        
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    # Get gender distribution
    gender_stats = {
        'Laki-laki': balita_stats['laki_laki'],
        'Perempuan': balita_stats['perempuan']
    }
    
    # Get age distribution
    age_stats = get_age_distribution()
    
    return {
        'months': months,
        'status_data': status_data,
        'gender_stats': gender_stats,
        'age_stats': age_stats
    }

def get_age_distribution():
    """Get age distribution of balita"""
    db = get_db()
    query = """
        SELECT 
            CASE 
                WHEN age < 12 THEN '0-1 tahun'
                WHEN age < 24 THEN '1-2 tahun'
                WHEN age < 36 THEN '2-3 tahun'
                WHEN age < 48 THEN '3-4 tahun'
                ELSE '4-5 tahun'
            END as age_group,
            COUNT(*) as count
        FROM (
            SELECT 
                CAST(
                    (julianday('now') - julianday(tanggal_lahir)) / 365.25 * 12 
                    as INTEGER
                ) as age
            FROM balita
        )
        GROUP BY age_group
        ORDER BY age_group
    """
    
    result = db.execute(query).fetchall()
    
    age_stats = {
        'labels': [],
        'data': []
    }
    
    for row in result:
        age_stats['labels'].append(row['age_group'])
        age_stats['data'].append(row['count'])
    
    return age_stats

@bp.route('/chart-data')
@login_required
def get_chart_data():
    """API endpoint untuk data chart"""
    # Get parameters
    chart_type = request.args.get('type', 'status')
    period = request.args.get('period', '30')  # days
    
    try:
        period = int(period)
    except ValueError:
        period = 30
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period)
    
    if chart_type == 'status':
        data = get_status_trend(start_date, end_date)
    elif chart_type == 'gender':
        data = get_gender_distribution()
    elif chart_type == 'age':
        data = get_age_distribution()
    else:
        data = {'error': 'Invalid chart type'}
    
    return jsonify(data)

@bp.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def format_number(value):
        """Format number with thousand separator"""
        try:
            return "{:,}".format(value)
        except (ValueError, TypeError):
            return value
    
    def get_status_color(status):
        """Get color for status"""
        colors = {
            'normal': '#28a745',
            'kurang': '#ffc107',
            'buruk': '#dc3545'
        }
        return colors.get(status.lower(), '#6c757d')
    
    return dict(
        format_number=format_number,
        get_status_color=get_status_color
    )