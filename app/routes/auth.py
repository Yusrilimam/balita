from flask import (
    Blueprint, flash, g, redirect, render_template, request, 
    session, url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from app.models.users import User
from app.utils.decorators import login_required, admin_required
import os
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
@admin_required
def register():
    """Register a new user (admin only)"""
    if request.method == 'POST':
        try:
            # Get form data
            user_data = {
                'username': request.form['username'],
                'password': request.form['password'],
                'nama_lengkap': request.form['nama_lengkap'],
                'email': request.form.get('email'),
                'role': request.form.get('role', 'user')
            }

            # Handle photo upload
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename:
                    filename = secure_filename(photo.filename)
                    ext = filename.rsplit('.', 1)[1].lower()
                    new_filename = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                    photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', new_filename)
                    photo.save(photo_path)
                    user_data['photo'] = new_filename

            # Create user
            User.create(user_data)
            flash('User berhasil didaftarkan.', 'success')
            return redirect(url_for('auth.manage_users'))

        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('Terjadi kesalahan saat mendaftarkan user.', 'danger')

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form

        try:
            user = User.authenticate(username, password)
            if user:
                session.clear()
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                session.permanent = remember

                flash(f'Selamat datang kembali, {user.nama_lengkap}!', 'success')
                return redirect(url_for('dashboard.index'))
            else:
                flash('Username atau password salah.', 'danger')

        except Exception as e:
            flash('Terjadi kesalahan saat login.', 'danger')

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/profile', methods=('GET', 'POST'))
@login_required
def profile():
    """User profile management"""
    user = User.get_by_id(session['user_id'])

    if request.method == 'POST':
        try:
            # Get form data
            update_data = {
                'nama_lengkap': request.form['nama_lengkap'],
                'email': request.form.get('email')
            }

            # Handle password change
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            if current_password and new_password:
                if User.change_password(user.id, current_password, new_password):
                    flash('Password berhasil diubah.', 'success')
                else:
                    flash('Password lama tidak sesuai.', 'danger')

            # Handle photo upload
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename:
                    # Delete old photo if exists
                    if user.photo and user.photo != 'default.jpg':
                        old_photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', user.photo)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)

                    # Save new photo
                    filename = secure_filename(photo.filename)
                    ext = filename.rsplit('.', 1)[1].lower()
                    new_filename = f"user_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                    photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', new_filename)
                    photo.save(photo_path)
                    update_data['photo'] = new_filename

            # Update user data
            if User.update(user.id, update_data):
                flash('Profil berhasil diperbarui.', 'success')
                return redirect(url_for('auth.profile'))

        except Exception as e:
            flash('Terjadi kesalahan saat memperbarui profil.', 'danger')

    return render_template('auth/profile.html', user=user)

@bp.route('/manage', methods=('GET',))
@admin_required
def manage_users():
    """Manage users (admin only)"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    users = User.get_all(search=search, page=page)
    return render_template('auth/manage_users.html', users=users, search=search)

@bp.route('/delete/<int:id>', methods=('POST',))
@admin_required
def delete_user(id):
    """Delete user (admin only)"""
    try:
        if User.delete(id):
            flash('User berhasil dihapus.', 'success')
        else:
            flash('Tidak dapat menghapus admin terakhir.', 'danger')
    except Exception as e:
        flash('Terjadi kesalahan saat menghapus user.', 'danger')

    return redirect(url_for('auth.manage_users'))

@bp.before_app_request
def load_logged_in_user():
    """Load user data before each request"""
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        g.user = User.get_by_id(user_id)

@bp.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def user_photo_url(filename):
        if filename:
            return url_for('static', filename=f'uploads/profiles/{filename}')
        return url_for('static', filename='img/default-profile.jpg')

    return dict(user_photo_url=user_photo_url)