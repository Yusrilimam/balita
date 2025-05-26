import click
from flask import Blueprint, g, render_template
from functools import wraps
from datetime import datetime

# Import blueprints
from .auth import bp as auth_bp
from .balita import bp as balita_bp
from .dashboard import bp as dashboard_bp
from .laporan import bp as laporan_bp
from .parameter import bp as parameter_bp
from .dataset import bp as dataset_bp

# List of blueprints with their URL prefixes and names
BLUEPRINTS = [
    (auth_bp, '/auth', 'auth'),
    (balita_bp, '/balita', 'balita'),
    (dashboard_bp, '/', 'dashboard'),
    (laporan_bp, '/laporan', 'laporan'),
    (parameter_bp, '/parameter', 'parameter'),
    (dataset_bp, '/dataset', 'dataset')
]

def init_app(app):
    """Initialize all blueprints and register before/after request handlers"""
    
    # Register all blueprints
    for blueprint, url_prefix, name in BLUEPRINTS:
        app.register_blueprint(blueprint, url_prefix=url_prefix)

    # Before request handler
    @app.before_request
    def before_request():
        """Actions to perform before each request"""
        # Set current time in UTC
        g.current_time = datetime.utcnow()
        
        # Set default page title
        g.page_title = "Sistem Monitoring Gizi Balita"
        
        # Set current year for footer
        g.current_year = datetime.utcnow().year
        
        # Set application version
        g.app_version = "1.0.0"

    # After request handler
    @app.after_request
    def after_request(response):
        """Actions to perform after each request"""
        # Enable CORS
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        
        return response

    # Template context processor
    @app.context_processor
    def utility_processor():
        """Add utility functions to template context"""
        def format_date(date):
            """Format date to readable string"""
            if date:
                return date.strftime('%d %B %Y')
            return ''

        def format_datetime(dt):
            """Format datetime to readable string"""
            if dt:
                return dt.strftime('%d %B %Y %H:%M')
            return ''

        def get_status_badge(status):
            """Get appropriate badge class for status"""
            badges = {
                'normal': 'success',
                'kurang': 'warning',
                'buruk': 'danger'
            }
            return badges.get(status.lower(), 'secondary')

        return dict(
            format_date=format_date,
            format_datetime=format_datetime,
            get_status_badge=get_status_badge,
            active_year=datetime.utcnow().year,
            app_name="Sistem Monitoring Gizi Balita",
            app_version="1.0.0"
        )

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        return render_template('errors/500.html'), 500

    # Custom CLI commands
    @app.cli.command('routes')
    def list_routes():
        """List all registered routes"""
        output = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            line = f"{rule.endpoint:30s} {methods:20s} {rule}"
            output.append(line)
        
        click.echo('\n'.join(sorted(output)))

    return app