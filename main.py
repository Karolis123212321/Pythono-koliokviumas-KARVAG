import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'application.db'

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    if user_id is not None:
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            return {'current_user': user['username']}
    return {'current_user': None}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone() is not None:
            error = f"User {username} is already registered."

        if error is None:
            db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                       (username, generate_password_hash(password)))
            db.commit()
            return redirect(url_for('login'))

        flash(error)

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user is None or not check_password_hash(user['password_hash'], password):
            error = 'Incorrect username or password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/tasks', methods=['GET', 'POST'])
def manage_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        user_id = session.get('user_id')
        if title and description:
            db.execute('INSERT INTO tasks (title, description, user_id) VALUES (?, ?, ?)', (title, description, user_id))
            db.commit()
        return redirect(url_for('manage_tasks'))
    tasks = db.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY id DESC', (session.get('user_id'),)).fetchall()
    return render_template('tasks.html', tasks=tasks)

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    db = get_db()
    task = db.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        status = request.form['status']
        db.execute('UPDATE tasks SET title = ?, description = ?, status = ? WHERE id = ?', (title, description, status, task_id))
        db.commit()
        return redirect(url_for('manage_tasks'))
    return render_template('edit_task.html', task=task)

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    db = get_db()
    db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()
    return redirect(url_for('manage_tasks'))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)