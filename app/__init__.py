import os
from flask import Flask, render_template
from flask_login import LoginManager
from datetime import timedelta

def create_app(test_config=None):
    # Create Flask app
    app = Flask(__name__, instance_relative_config=True)
    
    # Load default config
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'balita.sqlite'),
        UPLOAD_FOLDER=os.path.join(app.static_folder, 'uploads'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.update(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Ensure upload folders exist
    for folder in ['profiles', 'documents']:
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        try:
            os.makedirs(upload_path)
        except OSError:
            pass

    # Initialize database
    from . import database
    database.init_app(app)

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from .models.users import User
        return User.get_by_id(user_id)

    # Register blueprints
    from .routes import init_app as init_routes
    init_routes(app)

    # Template filters
    from .utils.helpers import format_date, format_datetime
    app.jinja_env.filters['date_format'] = format_date
    app.jinja_env.filters['datetime_format'] = format_datetime

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app