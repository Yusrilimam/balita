from flask import current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
import re

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, folder='uploads', allowed_extensions=None):
    """Save uploaded file and return filename"""
    if not file or not allowed_file(file.filename, allowed_extensions):
        raise ValueError('File type not allowed')
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    new_filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Create folder if not exists
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_folder, new_filename)
    file.save(file_path)
    
    return new_filename

def delete_file(filename, folder='uploads'):
    """Delete file from uploads folder"""
    if not filename:
        return False
    
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def format_date(date_str, input_format='%Y-%m-%d', output_format='%d %B %Y'):
    """Format date string"""
    try:
        date_obj = datetime.strptime(date_str, input_format)
        return date_obj.strftime(output_format)
    except:
        return date_str

def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    
    try:
        birth = datetime.strptime(birth_date, '%Y-%m-%d')
        today = datetime.utcnow()
        
        years = today.year - birth.year
        months = today.month - birth.month
        
        if today.day < birth.day:
            months -= 1
        
        if months < 0:
            years -= 1
            months += 12
            
        return {
            'years': years,
            'months': months
        }
    except:
        return None

def format_age(age_dict):
    """Format age dictionary to string"""
    if not age_dict:
        return ''
    
    years = age_dict.get('years', 0)
    months = age_dict.get('months', 0)
    
    if years == 0:
        return f"{months} bulan"
    return f"{years} tahun {months} bulan"

def sanitize_string(text):
    """Remove special characters from string"""
    if not text:
        return ''
    return re.sub(r'[^a-zA-Z0-9\s]', '', text)

def format_thousand(number):
    """Format number with thousand separator"""
    try:
        return "{:,}".format(number)
    except:
        return number

def get_status_badge(status):
    """Get Bootstrap badge class for status"""
    status_classes = {
        'normal': 'success',
        'kurang': 'warning',
        'buruk': 'danger',
        'pending': 'secondary',
        'active': 'primary',
        'inactive': 'secondary'
    }
    return f"badge badge-{status_classes.get(status.lower(), 'secondary')}"

def generate_chart_colors(n):
    """Generate n distinct colors for charts"""
    colors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#858796', '#5a5c69', '#2e59d9', '#17a673', '#2c9faf'
    ]
    return colors[:n] if n <= len(colors) else colors * (n // len(colors) + 1)

def flatten_dict(d, parent_key='', sep='_'):
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def paginate(items, page=1, per_page=10):
    """Paginate list of items"""
    total = len(items)
    pages = (total + per_page - 1) // per_page
    page = min(max(page, 1), pages)
    offset = (page - 1) * per_page
    
    return {
        'items': items[offset:offset + per_page],
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages,
        'has_prev': page > 1,
        'has_next': page < pages
    }