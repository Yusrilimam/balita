from functools import wraps
from flask import Response, flash, g, redirect, url_for, session, request
from datetime import datetime

from app.database import get_db

def login_required(view):
    """Decorator to verify user is logged in"""
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Anda harus login terlebih dahulu.', 'warning')
            # Store the requested URL for redirect after login
            session['next_url'] = request.url
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    """Decorator to verify user is admin"""
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Anda harus login terlebih dahulu.', 'warning')
            session['next_url'] = request.url
            return redirect(url_for('auth.login'))
        
        if not g.user.is_admin():
            flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
            return redirect(url_for('dashboard.index'))
            
        return view(**kwargs)
    return wrapped_view

def log_activity(activity_type):
    """Decorator to log user activity"""
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            # Execute the view
            response = view(**kwargs)
            
            # Log the activity if user is logged in
            if g.user:
                try:
                    log_data = {
                        'user_id': g.user.id,
                        'activity_type': activity_type,
                        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                        'url': request.url,
                        'method': request.method,
                        'ip_address': request.remote_addr
                    }
                    
                    db = get_db()
                    db.execute("""
                        INSERT INTO activity_logs 
                        (user_id, activity_type, timestamp, url, method, ip_address)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        log_data['user_id'],
                        log_data['activity_type'],
                        log_data['timestamp'],
                        log_data['url'],
                        log_data['method'],
                        log_data['ip_address']
                    ))
                    db.commit()
                except Exception:
                    # Silently fail if logging fails
                    pass
            
            return response
        return wrapped_view
    return decorator

def cache_control(*directives):
    """Decorator to set Cache-Control header"""
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            response = view(**kwargs)
            if isinstance(response, Response):
                response.headers['Cache-Control'] = ', '.join(directives)
            return response
        return wrapped_view
    return decorator

def validate_form(*required_fields):
    """Decorator to validate form fields"""
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if request.method == 'POST':
                missing_fields = []
                for field in required_fields:
                    if not request.form.get(field):
                        missing_fields.append(field)
                
                if missing_fields:
                    flash(f'Field berikut harus diisi: {", ".join(missing_fields)}', 'danger')
                    return redirect(request.url)
            
            return view(**kwargs)
        return wrapped_view
    return decorator