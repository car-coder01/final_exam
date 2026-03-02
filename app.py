from flask import Flask, request, jsonify, render_template
import jwt
import datetime
import hashlib
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jmeter-test-secret-key-2026'

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')


# ──────────────────────────────────────────────
#  SQLite DATABASE
# ──────────────────────────────────────────────
def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the users table if it doesn't exist."""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# Initialize database on startup
init_db()


# ──────────────────────────────────────────────
#  WEB PAGES (browser-friendly)
# ──────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('register.html')


@app.route('/register')
def register_page():
    return render_template('register.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')


def hash_password(password):
    """Hash password with SHA-256."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def generate_token(username):
    """Generate a JWT token for the given username."""
    payload = {
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def decode_token(token):
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ──────────────────────────────────────────────
#  REGISTER
# ──────────────────────────────────────────────
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400

    username = data['username'].strip()
    password = data['password'].strip()

    if len(username) < 3:
        return jsonify({'status': 'error', 'message': 'Username must be at least 3 characters'}), 400

    if len(password) < 6:
        return jsonify({'status': 'error', 'message': 'Password must be at least 6 characters'}), 400

    conn = get_db()
    existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Username already exists'}), 409

    created_at = datetime.datetime.utcnow().isoformat()
    conn.execute('INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)',
                 (username, hash_password(password), created_at))
    conn.commit()
    conn.close()

    return jsonify({
        'status': 'success',
        'message': f'User {username} registered successfully'
    }), 201


# ──────────────────────────────────────────────
#  LOGIN
# ──────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400

    username = data['username'].strip()
    password = data['password'].strip()

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if not user or user['password'] != hash_password(password):
        return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401

    token = generate_token(username)

    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'token': token
    }), 200


# ──────────────────────────────────────────────
#  DASHBOARD  (requires auth token)
# ──────────────────────────────────────────────
@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'status': 'error', 'message': 'Authorization token is required'}), 401

    token = auth_header.split(' ')[1]
    payload = decode_token(token)

    if not payload:
        return jsonify({'status': 'error', 'message': 'Invalid or expired token'}), 401

    username = payload['username']

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    conn.close()

    return jsonify({
        'status': 'success',
        'message': f'Welcome to the dashboard, {username}!',
        'data': {
            'username': username,
            'registered_at': user['created_at'] if user else 'unknown',
            'total_users': total_users,
            'server_time': datetime.datetime.utcnow().isoformat()
        }
    }), 200


# ──────────────────────────────────────────────
#  HEALTH CHECK
# ──────────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def health():
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    conn.close()
    return jsonify({'status': 'ok', 'users_count': count}), 200


if __name__ == '__main__':
    print("=" * 50)
    print("  Flask Auth API - JMeter Test Server")
    print("  Running on http://localhost:5000")
    print("=" * 50)
    print("\nEndpoints:")
    print("  POST /api/register  - Register a new user")
    print("  POST /api/login     - Login and get JWT token")
    print("  GET  /api/dashboard - Protected dashboard")
    print("  GET  /api/health    - Health check")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
