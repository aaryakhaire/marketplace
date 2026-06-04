from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os
import secrets
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'velora-secret-xk9p-2026-street'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')


# ---------- HELPERS ----------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(stored, provided):
    try:
        salt, hashed = stored.split(':', 1)
        return hashlib.sha256((salt + provided).encode()).hexdigest() == hashed
    except Exception:
        return False


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def current_user():
    """Return the logged-in user row, or None."""
    if 'user_id' not in session:
        return None
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return user


# ---------- DATABASE ----------

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar_seed TEXT,
            joined_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Items / listings table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            price TEXT,
            image TEXT,
            contact TEXT,
            category TEXT DEFAULT 'Streetwear',
            seller_id INTEGER REFERENCES users(id),
            is_sold INTEGER DEFAULT 0
        )
    """)

    # Migrate existing items table — add new columns if missing
    cur.execute("PRAGMA table_info(items)")
    existing_cols = [row[1] for row in cur.fetchall()]
    if 'category' not in existing_cols:
        cur.execute("ALTER TABLE items ADD COLUMN category TEXT DEFAULT 'Streetwear'")
    if 'seller_id' not in existing_cols:
        cur.execute("ALTER TABLE items ADD COLUMN seller_id INTEGER REFERENCES users(id)")
    if 'is_sold' not in existing_cols:
        cur.execute("ALTER TABLE items ADD COLUMN is_sold INTEGER DEFAULT 0")

    # Transactions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER REFERENCES users(id),
            seller_id INTEGER REFERENCES users(id),
            item_id INTEGER REFERENCES items(id),
            item_title TEXT,
            item_image TEXT,
            price_at_purchase TEXT,
            status TEXT DEFAULT 'Confirmed',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Seed sample items if none exist
    cur.execute("SELECT COUNT(*) FROM items")
    if cur.fetchone()[0] == 0:
        sample_items = [
            ("Black Hoodie", "Premium oversized hoodie, unisex fit", "₹2499",
             "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600", "9999999999", "Hoodie", None),
            ("Street Jacket", "Urban bomber jacket in matte black", "₹3999",
             "https://images.unsplash.com/photo-1516826957135-700dedea698c?w=600", "9999999999", "Jacket", None),
            ("Minimal Tee", "Clean white street tee, 100% cotton", "₹999",
             "https://images.unsplash.com/photo-1520975922071-a7f63a5e6a4c?w=600", "9999999999", "T-Shirt", None),
            ("Cargo Pants", "Relaxed fit cargo pants with side pockets", "₹2799",
             "https://images.unsplash.com/photo-1520975867597-0af37a22e31a?w=600", "9999999999", "Pants", None),
            ("Sneakers", "Modern low-top street sneakers", "₹5499",
             "https://images.unsplash.com/photo-1528701800489-20be3c66a93c?w=600", "9999999999", "Sneakers", None),
        ]
        cur.executemany(
            "INSERT INTO items (title, description, price, image, contact, category, seller_id) VALUES (?,?,?,?,?,?,?)",
            sample_items
        )

    conn.commit()
    conn.close()


# ---------- CONTEXT PROCESSOR ----------

@app.context_processor
def inject_user():
    return dict(current_user=current_user())


# ---------- AUTH ROUTES ----------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        conn = get_db()
        existing = conn.execute(
            'SELECT id FROM users WHERE email = ? OR username = ?', (email, username)
        ).fetchone()

        if existing:
            conn.close()
            flash('An account with that email or username already exists.', 'error')
            return render_template('register.html')

        seed = username.replace(' ', '_')
        conn.execute(
            'INSERT INTO users (username, email, password_hash, avatar_seed) VALUES (?, ?, ?, ?)',
            (username, email, hash_password(password), seed)
        )
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        session['user_id'] = user['id']
        session['username'] = user['username']
        flash(f"Welcome to Velora, {username}!", 'success')
        return redirect(url_for('profile'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('profile'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and verify_password(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f"Welcome back, {user['username']}!", 'success')
            return redirect(request.args.get('next') or url_for('profile'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ---------- MAIN ROUTES ----------

@app.route('/')
def index():
    search = request.args.get('search', '')
    conn = get_db()

    if search:
        items = conn.execute(
            "SELECT i.*, u.username as seller_name FROM items i LEFT JOIN users u ON i.seller_id = u.id "
            "WHERE (i.title LIKE ? OR i.description LIKE ?) AND i.is_sold = 0",
            (f'%{search}%', f'%{search}%')
        ).fetchall()
    else:
        items = conn.execute(
            "SELECT i.*, u.username as seller_name FROM items i LEFT JOIN users u ON i.seller_id = u.id "
            "WHERE i.is_sold = 0 LIMIT 12"
        ).fetchall()

    conn.close()
    return render_template('index.html', items=items, search=search)


@app.route('/explore')
def explore():
    category = request.args.get('category', '')
    conn = get_db()

    categories = [row[0] for row in conn.execute(
        "SELECT DISTINCT category FROM items WHERE is_sold = 0"
    ).fetchall()]

    if category:
        items = conn.execute(
            "SELECT i.*, u.username as seller_name FROM items i LEFT JOIN users u ON i.seller_id = u.id "
            "WHERE i.category = ? AND i.is_sold = 0",
            (category,)
        ).fetchall()
    else:
        items = conn.execute(
            "SELECT i.*, u.username as seller_name FROM items i LEFT JOIN users u ON i.seller_id = u.id "
            "WHERE i.is_sold = 0"
        ).fetchall()

    conn.close()
    return render_template('explore.html', items=items, categories=categories, active_cat=category)


@app.route('/contact')
def contact():
    return render_template('contact_us.html')


# ---------- LISTING ROUTES ----------

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post_item():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', '').strip()
        image = request.form.get('image', '').strip()
        contact = request.form.get('contact', '').strip()
        category = request.form.get('category', 'Streetwear').strip()

        if not title or not price:
            flash('Title and price are required.', 'error')
            return render_template('post.html')

        # Prepend ₹ if not already present
        if price and not price.startswith('₹'):
            price = '₹' + price

        conn = get_db()
        conn.execute(
            "INSERT INTO items (title, description, price, image, contact, category, seller_id) VALUES (?,?,?,?,?,?,?)",
            (title, description, price, image, contact, category, session['user_id'])
        )
        conn.commit()
        conn.close()

        flash(f'"{title}" is now live on Velora!', 'success')
        return redirect(url_for('profile'))

    return render_template('post.html')


# ---------- BUY / TRANSACTIONS ----------

@app.route('/buy/<int:item_id>', methods=['POST'])
@login_required
def buy_item(item_id):
    conn = get_db()
    item = conn.execute('SELECT * FROM items WHERE id = ? AND is_sold = 0', (item_id,)).fetchone()

    if not item:
        flash('This item is no longer available.', 'error')
        conn.close()
        return redirect(url_for('explore'))

    if item['seller_id'] == session['user_id']:
        flash("You can't buy your own listing.", 'error')
        conn.close()
        return redirect(url_for('explore'))

    # Create transaction
    conn.execute(
        """INSERT INTO transactions
           (buyer_id, seller_id, item_id, item_title, item_image, price_at_purchase, status)
           VALUES (?, ?, ?, ?, ?, ?, 'Confirmed')""",
        (session['user_id'], item['seller_id'], item_id,
         item['title'], item['image'], item['price'])
    )

    # Mark item as sold
    conn.execute('UPDATE items SET is_sold = 1 WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()

    flash(f'🎉 You bought "{item["title"]}"! Check your orders.', 'success')
    return redirect(url_for('orders'))


# ---------- USER ROUTES ----------

@app.route('/profile')
@login_required
def profile():
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    # User's own listings
    my_listings = conn.execute(
        "SELECT * FROM items WHERE seller_id = ? ORDER BY id DESC",
        (session['user_id'],)
    ).fetchall()

    # User's purchases
    my_purchases = conn.execute(
        "SELECT t.*, i.image FROM transactions t LEFT JOIN items i ON t.item_id = i.id "
        "WHERE t.buyer_id = ? ORDER BY t.created_at DESC",
        (session['user_id'],)
    ).fetchall()

    conn.close()
    return render_template('profile.html', user=user, my_listings=my_listings, my_purchases=my_purchases)


@app.route('/orders')
@login_required
def orders():
    conn = get_db()
    transactions = conn.execute(
        """SELECT t.*, u.username as seller_name
           FROM transactions t
           LEFT JOIN users u ON t.seller_id = u.id
           WHERE t.buyer_id = ?
           ORDER BY t.created_at DESC""",
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return render_template('orders.html', transactions=transactions)


# ---------- RUN ----------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
