import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g
from datetime import datetime

DATABASE = 'application.db'

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.context_processor
def inject_user():
    user = session.get('username', None)
    return dict(current_user=user)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/setuser', methods=['POST'])
def setuser():
    session['username'] = request.form['username']
    return redirect(url_for('index'))

@app.route('/tasks', methods=['GET', 'POST'])
def manage_tasks():
    db = get_db()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        user_name = session.get('username')
        if title and description and user_name:
            db.execute('INSERT INTO tasks (title, description, user_name) VALUES (?, ?, ?)', (title, description, user_name))
            db.commit()
        return redirect(url_for('manage_tasks'))
    tasks = db.execute('SELECT * FROM tasks ORDER BY id DESC').fetchall()
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
