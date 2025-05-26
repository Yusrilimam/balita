from app import create_app
from flask.cli import FlaskGroup
import click
import os

app = create_app()
cli = FlaskGroup(app)

@cli.command('init-db')
def init_db():
    """Initialize the database."""
    from app.database import init_db
    init_db()
    click.echo('Initialized the database.')

@cli.command('create-admin')
@click.argument('username')
@click.argument('password')
def create_admin(username, password):
    """Create an admin user."""
    from app.models.users import User
    try:
        user_data = {
            'username': username,
            'password': password,
            'nama_lengkap': 'Administrator',
            'role': 'admin'
        }
        User.create(user_data)
        click.echo(f'Created admin user: {username}')
    except Exception as e:
        click.echo(f'Error creating admin user: {str(e)}', err=True)

@cli.command('reset-db')
@click.confirmation_option(prompt='Are you sure you want to reset the database?')
def reset_db():
    """Reset the database."""
    from app.database import init_db
    db_path = os.path.join(app.instance_path, 'gizi_balita.sqlite')
    if os.path.exists(db_path):
        os.unlink(db_path)
        click.echo('Removed existing database.')
    init_db()
    click.echo('Initialized new database.')

@cli.command('seed-db')
def seed_db():
    """Seed the database with sample data."""
    from app.models.users import User
    from app.models.balita import Balita
    from app.models.pengukuran import Pengukuran
    from datetime import datetime, timedelta
    import random

    try:
        # Create admin user if not exists
        if not User.get_by_username('admin'):
            User.create({
                'username': 'admin',
                'password': 'admin123',
                'nama_lengkap': 'Administrator',
                'role': 'admin'
            })

        # Create sample balita
        for i in range(10):
            # Random birth date between 0-5 years ago
            days_ago = random.randint(0, 5*365)
            birth_date = datetime.now() - timedelta(days=days_ago)
            
            balita_data = {
                'nik': f'35150{i:08d}',
                'nama': f'Balita Test {i+1}',
                'tanggal_lahir': birth_date.strftime('%Y-%m-%d'),
                'jenis_kelamin': random.choice(['L', 'P']),
                'nama_ortu': f'Orang Tua {i+1}',
                'alamat': f'Alamat Test {i+1}'
            }
            
            balita_id = Balita.create(balita_data)
            
            # Create sample pengukuran
            for j in range(random.randint(3, 6)):
                # Random measurement date after birth date
                measurement_days = random.randint(30, (datetime.now() - birth_date).days)
                measurement_date = birth_date + timedelta(days=measurement_days)
                
                pengukuran_data = {
                    'balita_id': balita_id,
                    'tanggal_ukur': measurement_date.strftime('%Y-%m-%d'),
                    'berat_badan': random.uniform(3.0, 15.0),
                    'tinggi_badan': random.uniform(45.0, 110.0),
                    'lingkar_lengan': random.uniform(10.0, 20.0),
                    'status_gizi': random.choice(['normal', 'kurang', 'buruk'])
                }
                
                Pengukuran.create(pengukuran_data)

        click.echo('Database seeded successfully.')
    except Exception as e:
        click.echo(f'Error seeding database: {str(e)}', err=True)

if __name__ == '__main__':
    cli()