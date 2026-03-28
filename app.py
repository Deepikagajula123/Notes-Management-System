from flask import Flask, render_template, request, redirect, session,flash
import sqlite3
import os
def get_db():
    import os

    # folder where app.py is located
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # database file path
    db_path = os.path.join(base_dir, "database.db")
    print("DB PATH:", db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Mail Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'deepikagajula6@gmail.com'
app.config['MAIL_PASSWORD'] = 'ecqo soxd ihmh mqkt'

mail = Mail(app)

# Upload Folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads')
# ================= DATABASE =================



def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT,
        profile_pic TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        content TEXT,
        pinned INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

# ================= ROUTES =================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user'] = user['id']
            session['username'] = user['username']
            return redirect('/dashboard')
        else:
            return render_template("login.html", error="Invalid login!")

    return render_template("login.html")


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users(username,email,password) VALUES(?,?,?)",
                (username, email, password)
            )

            conn.commit()
            conn.close()
            flash("Registration successful! Please login.", "success")
            return redirect('/')
        except sqlite3.IntegrityError:
            conn.close()
            flash("Email already registered!", "danger")
    return render_template("register.html",error="Email already exists!")


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template("dashboard.html")


@app.route('/addnote', methods=['GET','POST'])
def addnote():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO notes(user_id,title,content) VALUES(?,?,?)",
            (session['user'], title, content)
        )

        conn.commit()
        conn.close()

        return redirect('/viewnotes')

    return render_template("addnote.html")


@app.route('/viewnotes')
def viewnotes():
    if 'user' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor()

    
    cursor.execute("""
    SELECT id, user_id, title, content,pinned,
    datetime(created_at) as created_at
    FROM notes
    WHERE user_id=?
    ORDER BY pinned DESC, created_at DESC
    """, (session['user'],))

    notes = cursor.fetchall()
    conn.close()

    return render_template("viewnotes.html", notes=notes)


@app.route('/note/<int:id>')
def single_note(id):
    if 'user' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM notes WHERE id=? AND user_id=?",
        (id, session['user'])
    )

    note = cursor.fetchone()
    conn.close()

    return render_template("singlenote.html", note=note)


@app.route('/profile', methods=['GET','POST'])
def profile():
    if 'user' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        file = request.files['photo']

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            cursor.execute(
                "UPDATE users SET profile_pic=? WHERE id=?",
                (filename, session['user'])
            )

            conn.commit()

    cursor.execute(
        "SELECT username,email,profile_pic FROM users WHERE id=?",
        (session['user'],)
    )

    user = cursor.fetchone()
    conn.close()

    return render_template("profile.html", user=user)


@app.route('/pin/<int:id>')
def pin_note(id):
    if 'user' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT pinned FROM notes WHERE id=?", (id,))
    note = cursor.fetchone()

    new_status = 0 if note['pinned'] == 1 else 1

    cursor.execute(
        "UPDATE notes SET pinned=? WHERE id=? AND user_id=?",
        (new_status, id, session['user'])
    )

    conn.commit()
    conn.close()

    return redirect('/viewnotes')


@app.route('/delete/<int:id>')
def delete_note(id):
    if 'user' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM notes WHERE id=? AND user_id=?",
        (id, session['user'])
    )

    conn.commit()
    conn.close()

    return redirect('/viewnotes')


@app.route('/update/<int:id>', methods=['GET','POST'])
def update_note(id):
    if 'user' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        cursor.execute(
            "UPDATE notes SET title=?, content=? WHERE id=? AND user_id=?",
            (title, content, id, session['user'])
        )

        conn.commit()
        conn.close()

        return redirect('/viewnotes')

    cursor.execute(
        "SELECT * FROM notes WHERE id=? AND user_id=?",
        (id, session['user'])
    )

    note = cursor.fetchone()
    conn.close()

    return render_template("updatenote.html", note=note)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/about')
def about():
    return render_template("about.html")


# @app.route('/contact', methods=['GET','POST'])
# def contact():
#     if request.method == 'POST':
#         name = request.form['name']
#         email = request.form['email']
#         message = request.form['message']

#         admin_msg = Message(
#             subject="New Contact Message",
#             sender=app.config['MAIL_USERNAME'],
#             recipients=['deepikagajula6@gmail.com']
#         )

#         admin_msg.body = f"""
# Name: {name}
# Email: {email}

# Message:
# {message}
# """
#         mail.send(admin_msg)

#         user_msg = Message(
#             subject="Thank you for contacting us",
#             sender=app.config['MAIL_USERNAME'],
#             recipients=[email]
#         )

#         user_msg.body = f"""
# Hello {name},

# Thank you for contacting us.
# We will get back to you soon.
# """
#         mail.send(user_msg)

#         return render_template("contact.html", success="Message sent successfully!")

#     return render_template("contact.html")


# ================= RUN =================
init_db() 
if __name__ == "__main__":
      # 🔥 VERY IMPORTANT
    app.run(debug=True)