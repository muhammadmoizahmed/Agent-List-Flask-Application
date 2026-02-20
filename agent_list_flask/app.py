from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import time
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_env():
    env_path = os.path.join(BASE_DIR, '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


load_env()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change_this_secret_in_env')

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database setup
def get_db_connection():
    conn = sqlite3.connect('database.db', timeout=5, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    conn = get_db_connection()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            whatsapp_number TEXT NOT NULL,
            phone_number TEXT,
            country TEXT NOT NULL,
            agent_custom_id TEXT,
            category TEXT DEFAULT 'Admin',
            rating INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    columns = conn.execute('PRAGMA table_info(agents)').fetchall()
    column_names = [col['name'] for col in columns]
    if 'country' not in column_names:
        conn.execute('ALTER TABLE agents ADD COLUMN country TEXT DEFAULT "N/A"')
    if 'phone_number' not in column_names:
        conn.execute('ALTER TABLE agents ADD COLUMN phone_number TEXT')
    if 'agent_custom_id' not in column_names:
        conn.execute('ALTER TABLE agents ADD COLUMN agent_custom_id TEXT')
    if 'city' in column_names:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS agents_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                whatsapp_number TEXT NOT NULL,
                phone_number TEXT,
                country TEXT NOT NULL,
                agent_custom_id TEXT,
                category TEXT DEFAULT 'Admin',
                rating INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            INSERT INTO agents_new (id, name, whatsapp_number, phone_number, country, agent_custom_id, category, rating, created_at)
            SELECT id, name, whatsapp_number, phone_number, 
                   CASE WHEN country IS NULL OR country = '' THEN 'N/A' ELSE country END,
                   agent_custom_id, category, rating, created_at
            FROM agents
        ''')
        conn.execute('DROP TABLE agents')
        conn.execute('ALTER TABLE agents_new RENAME TO agents')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS logos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            title TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    admin = conn.execute('SELECT * FROM admins WHERE username = ?', (admin_username,)).fetchone()
    if not admin:
        hashed_password = generate_password_hash(admin_password)
        conn.execute('INSERT INTO admins (username, password) VALUES (?, ?)', 
                    (admin_username, hashed_password))
    
    conn.commit()
    conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    conn = get_db_connection()
    agents = conn.execute('SELECT * FROM agents ORDER BY name').fetchall()
    logos = conn.execute('SELECT * FROM logos WHERE is_active = 1 ORDER BY id').fetchall()
    
    # Count agents by category
    all_count = conn.execute('SELECT COUNT(*) FROM agents').fetchone()[0]
    admin_count = conn.execute('SELECT COUNT(*) FROM agents WHERE category = "Admin"').fetchone()[0]
    subadmin_count = conn.execute('SELECT COUNT(*) FROM agents WHERE category = "SubAdmin"').fetchone()[0]
    super_count = conn.execute('SELECT COUNT(*) FROM agents WHERE category = "Super"').fetchone()[0]
    master_count = conn.execute('SELECT COUNT(*) FROM agents WHERE category = "Master"').fetchone()[0]
    
    conn.close()
    
    # Load page title
    page_title = 'SkyFairx & baajiX365 Official Agent List'
    try:
        with open('page_title.txt', 'r', encoding='utf-8') as f:
            page_title = f.read().strip()
    except:
        pass
    
    # Load info data
    info_data = {
        'main_title': 'ভিডিও দেখে খেলুন এবং জিতুন',
        'description': 'অ্যাকাউন্ট খোলার জন্য আমাদের এজেন্টদের সাথে যোগাযোগ করুন। আমাদের এজেন্টরা আপনাকে অ্যাকাউন্ট খুলতে সাহায্য করবে।',
        'warning': 'অ্যাকাউন্ট খোলার আগে এজেন্টের সাথে ভালোভাবে কথা বলে নিন। আমাদের এজেন্টরা সবসময় আপনার সাহায্যে প্রস্তুত।',
        'deposit_info': 'সর্বনিম্ন ডিপোজিট: 500 টাকা\nসর্বনিম্ন উইথড্র: 1000 টাকা\nউইথড্র সময়: 5-10 মিনিট\n24/7 সাপোর্ট উপলব্ধ'
    }
    
    # Try to load from file if exists
    try:
        with open('info_content.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith('MAIN_TITLE:'):
                    info_data['main_title'] = line.replace('MAIN_TITLE:', '')
                elif line.startswith('DESCRIPTION:'):
                    info_data['description'] = line.replace('DESCRIPTION:', '')
                elif line.startswith('WARNING:'):
                    info_data['warning'] = line.replace('WARNING:', '')
                elif line.startswith('DEPOSIT_INFO:'):
                    info_data['deposit_info'] = line.replace('DEPOSIT_INFO:', '')
    except:
        pass
    
    return render_template('index.html', agents=agents, info_data=info_data, page_title=page_title,
                       logos=logos,
                       all_count=all_count,
                       admin_count=admin_count,
                       subadmin_count=subadmin_count,
                       super_count=super_count,
                       master_count=master_count)

@app.route('/admin')
@login_required
def admin():
    conn = get_db_connection()
    agents = conn.execute('SELECT * FROM agents ORDER BY name').fetchall()
    
    # Count agents by category
    admin_count = conn.execute('SELECT COUNT(*) FROM agents WHERE category = "Admin"').fetchone()[0]
    subadmin_count = conn.execute('SELECT COUNT(*) FROM agents WHERE category = "SubAdmin"').fetchone()[0]
    super_count = conn.execute('SELECT COUNT(*) FROM agents WHERE category = "Super"').fetchone()[0]
    master_count = conn.execute('SELECT COUNT(*) FROM agents WHERE category = "Master"').fetchone()[0]
    user_count = conn.execute('SELECT COUNT(*) FROM agents WHERE category != "Admin"').fetchone()[0]
    
    conn.close()
    
    # Convert sqlite3.Row objects to dictionaries
    agents_list = []
    for agent in agents:
        agent_dict = dict(agent)
        if agent_dict['created_at']:
            agent_dict['created_at'] = str(agent_dict['created_at'])
        agents_list.append(agent_dict)
    
    return render_template('admin.html', agents=agents_list, 
                       admin_count=admin_count, 
                       subadmin_count=subadmin_count,
                       super_count=super_count,
                       master_count=master_count,
                       user_count=user_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            flash('Login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/add_agent', methods=['GET', 'POST'])
@login_required
def add_agent():
    if request.method == 'POST':
        name = request.form['name']
        agent_custom_id = request.form['agent_custom_id'].strip()
        whatsapp_number = request.form['whatsapp_number']
        phone_number = request.form.get('phone_number', '').strip()
        country = request.form.get('country', 'N/A')
        category = request.form['category']
        rating = request.form['rating']
        
        if not name or not agent_custom_id or not whatsapp_number or not category or not rating:
            flash('All fields are required', 'danger')
            return render_template('add_agent.html')
        
        conn = get_db_connection()
        try:
            existing = conn.execute('SELECT id FROM agents WHERE agent_custom_id = ?', (agent_custom_id,)).fetchone()
            if existing:
                flash('This Agent ID is already in use. Please choose another.', 'danger')
                return render_template('add_agent.html')
            
            conn.execute(
                'INSERT INTO agents (name, whatsapp_number, phone_number, country, agent_custom_id, category, rating) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (name, whatsapp_number, phone_number, country, agent_custom_id, category, int(rating))
            )
            conn.commit()
        except sqlite3.OperationalError as e:
            conn.rollback()
            if 'locked' in str(e).lower():
                flash('Database is busy. Please try again in a few seconds.', 'danger')
                return render_template('add_agent.html')
            raise
        finally:
            conn.close()
        
        flash('Agent added successfully!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('add_agent.html')

@app.route('/edit_agent/<int:agent_id>', methods=['GET', 'POST'])
@login_required
def edit_agent(agent_id):
    conn = get_db_connection()
    agent = conn.execute('SELECT * FROM agents WHERE id = ?', (agent_id,)).fetchone()
    
    if not agent:
        conn.close()
        flash('Agent not found', 'danger')
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        name = request.form['name']
        agent_custom_id = request.form['agent_custom_id'].strip()
        whatsapp_number = request.form['whatsapp_number']
        phone_number = request.form.get('phone_number', '').strip()
        country = agent['country']
        category = request.form['category']
        rating = request.form['rating']
        
        if not name or not agent_custom_id or not whatsapp_number or not category or not rating:
            flash('All fields are required', 'danger')
            conn.close()
            return render_template('edit_agent.html', agent=agent)
        
        existing = conn.execute(
            'SELECT id FROM agents WHERE agent_custom_id = ? AND id != ?',
            (agent_custom_id, agent_id)
        ).fetchone()
        if existing:
            conn.close()
            flash('This Agent ID is already in use. Please choose another.', 'danger')
            return render_template('edit_agent.html', agent=agent)
        
        conn.execute(
            'UPDATE agents SET name = ?, whatsapp_number = ?, phone_number = ?, country = ?, agent_custom_id = ?, category = ?, rating = ? WHERE id = ?',
            (name, whatsapp_number, phone_number, country, agent_custom_id, category, int(rating), agent_id)
        )
        conn.commit()
        conn.close()
        
        flash('Agent updated successfully!', 'success')
        return redirect(url_for('admin'))
    
    conn.close()
    return render_template('edit_agent.html', agent=agent)

@app.route('/delete_agent/<int:agent_id>')
@login_required
def delete_agent(agent_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM agents WHERE id = ?', (agent_id,))
    conn.commit()
    conn.close()
    
    flash('Agent deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/upload_logo', methods=['GET', 'POST'])
@login_required
def upload_logo():
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No files selected', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            flash('No files selected', 'danger')
            return redirect(request.url)
        
        saved_count = 0
        conn = get_db_connection()
        for file in files:
            if not file or file.filename == '':
                continue
            if not allowed_file(file.filename):
                continue
            original_name = secure_filename(file.filename)
            unique_name = f"{int(time.time() * 1000)}_{original_name}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(save_path)
            title = os.path.splitext(original_name)[0]
            conn.execute(
                'INSERT INTO logos (filename, title, is_active) VALUES (?, ?, ?)',
                (unique_name, title, 1)
            )
            saved_count += 1
        conn.commit()
        conn.close()
        
        if saved_count > 0:
            flash(f'{saved_count} logo(s) uploaded successfully!', 'success')
        else:
            flash('No valid image files selected.', 'danger')
        
        return redirect(url_for('upload_logo'))
    
    conn = get_db_connection()
    logos = conn.execute('SELECT * FROM logos ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('upload_logo.html', logos=logos)


@app.route('/delete_logo/<int:logo_id>')
@login_required
def delete_logo(logo_id):
    conn = get_db_connection()
    logo = conn.execute('SELECT * FROM logos WHERE id = ?', (logo_id,)).fetchone()
    if logo:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], logo['filename'])
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
        conn.execute('DELETE FROM logos WHERE id = ?', (logo_id,))
        conn.commit()
        flash('Logo deleted successfully!', 'success')
    else:
        flash('Logo not found', 'danger')
    conn.close()
    return redirect(url_for('upload_logo'))


@app.route('/edit_logo/<int:logo_id>', methods=['POST'])
@login_required
def edit_logo(logo_id):
    title = request.form.get('title', '').strip()
    is_active = 1 if request.form.get('is_active') == 'on' else 0
    
    conn = get_db_connection()
    logo = conn.execute('SELECT * FROM logos WHERE id = ?', (logo_id,)).fetchone()
    if not logo:
        conn.close()
        flash('Logo not found', 'danger')
        return redirect(url_for('upload_logo'))
    
    conn.execute(
        'UPDATE logos SET title = ?, is_active = ? WHERE id = ?',
        (title or None, is_active, logo_id)
    )
    conn.commit()
    conn.close()
    flash('Logo updated successfully!', 'success')
    return redirect(url_for('upload_logo'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required', 'danger')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return render_template('change_password.html')
        
        # Verify current password
        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE id = ?', (session['admin_id'],)).fetchone()
        conn.close()
        
        if not check_password_hash(admin['password'], current_password):
            flash('Current password is incorrect', 'danger')
            return render_template('change_password.html')
        
        # Update password
        hashed_password = generate_password_hash(new_password)
        conn = get_db_connection()
        conn.execute('UPDATE admins SET password = ? WHERE id = ?', (hashed_password, session['admin_id']))
        conn.commit()
        conn.close()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('change_password.html')

@app.route('/edit_info', methods=['GET', 'POST'])
@login_required
def edit_info():
    if request.method == 'POST':
        main_title = request.form['main_title']
        description = request.form['description']
        warning = request.form['warning']
        deposit_info = request.form['deposit_info']
        
        # Save to a simple text file for now (can be moved to database later)
        with open('info_content.txt', 'w', encoding='utf-8') as f:
            f.write(f"MAIN_TITLE:{main_title}\n")
            f.write(f"DESCRIPTION:{description}\n")
            f.write(f"WARNING:{warning}\n")
            f.write(f"DEPOSIT_INFO:{deposit_info}\n")
        
        flash('Information updated successfully!', 'success')
        return redirect(url_for('admin'))
    
    # Load current info
    current_info = {
        'main_title': 'ভিডিও দেখে খেলুন এবং জিতুন',
        'description': 'অ্যাকাউন্ট খোলার জন্য আমাদের এজেন্টদের সাথে যোগাযোগ করুন। আমাদের এজেন্টরা আপনাকে অ্যাকাউন্ট খুলতে সাহায্য করবে।',
        'warning': 'অ্যাকাউন্ট খোলার আগে এজেন্টের সাথে ভালোভাবে কথা বলে নিন। আমাদের এজেন্টরা সবসময় আপনার সাহায্যে প্রস্তুত।',
        'deposit_info': 'সর্বনিম্ন ডিপোজিট: 500 টাকা\nসর্বনিম্ন উইথড্র: 1000 টাকা\nউইথড্র সময়: 5-10 মিনিট\n24/7 সাপোর্ট উপলব্ধ'
    }
    
    # Try to load from file if exists
    try:
        with open('info_content.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith('MAIN_TITLE:'):
                    current_info['main_title'] = line.replace('MAIN_TITLE:', '')
                elif line.startswith('DESCRIPTION:'):
                    current_info['description'] = line.replace('DESCRIPTION:', '')
                elif line.startswith('WARNING:'):
                    current_info['warning'] = line.replace('WARNING:', '')
                elif line.startswith('DEPOSIT_INFO:'):
                    current_info['deposit_info'] = line.replace('DEPOSIT_INFO:', '')
    except:
        pass
    
    return render_template('edit_info.html', **current_info)

@app.route('/change_title', methods=['GET', 'POST'])
@login_required
def change_title():
    if request.method == 'POST':
        page_title = request.form['page_title']
        
        if not page_title:
            flash('Page title is required', 'danger')
            return render_template('change_title.html', current_title='SkyFairx & baajiX365 Official Agent List')
        
        # Save to text file
        with open('page_title.txt', 'w', encoding='utf-8') as f:
            f.write(page_title)
        
        flash('Page title updated successfully!', 'success')
        return redirect(url_for('admin'))
    
    # Load current title
    current_title = 'SkyFairx & baajiX365 Official Agent List'
    try:
        with open('page_title.txt', 'r', encoding='utf-8') as f:
            current_title = f.read().strip()
    except:
        pass
    
    return render_template('change_title.html', current_title=current_title)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
