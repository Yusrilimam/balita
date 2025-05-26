import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    """Initialize database"""
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    """Register database functions with the Flask app"""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def query_db(query, args=(), one=False):
    """Query helper function"""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def insert_db(table, fields=None):
    """Insert helper function"""
    if not fields:
        return None
        
    keys = ', '.join(fields.keys())
    values = ', '.join(['?' for _ in fields])
    sql = f'INSERT INTO {table} ({keys}) VALUES ({values})'
    
    try:
        db = get_db()
        cur = db.execute(sql, list(fields.values()))
        db.commit()
        return cur.lastrowid
    except Exception as e:
        db.rollback()
        raise e

def update_db(table, fields=None, condition=None):
    """Update helper function"""
    if not fields or not condition:
        return False
        
    set_clause = ', '.join([f'{key} = ?' for key in fields.keys()])
    where_clause = ' AND '.join([f'{key} = ?' for key in condition.keys()])
    sql = f'UPDATE {table} SET {set_clause} WHERE {where_clause}'
    
    try:
        db = get_db()
        db.execute(sql, list(fields.values()) + list(condition.values()))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e

def delete_db(table, condition=None):
    """Delete helper function"""
    if not condition:
        return False
        
    where_clause = ' AND '.join([f'{key} = ?' for key in condition.keys()])
    sql = f'DELETE FROM {table} WHERE {where_clause}'
    
    try:
        db = get_db()
        db.execute(sql, list(condition.values()))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e