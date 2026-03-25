from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'deepikagajula6@gmail.com'
app.config['MAIL_PASSWORD'] = 'ecqo soxd ihmh mqkt'

mail = Mail(app)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
# Database connection
db = mysql.connector.connect(
    host="Deepika123.mysql.pythonanywhere-services.com",
    user="root",
    password="root",
    database="notes",
    charset='utf8'
)

cursor = db.cursor()

# ================= ROUTES =================

# Login Page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):
            session['user'] = user[0]  # user id
            session['username'] = user[1]
            return redirect('/dashboard')
        else:
            return render_template("login.html", error="Invalid login!")

    return render_template("login.html")

# Register Page
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cursor.execute("INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",
                       (username,email,password))
        db.commit()
        return redirect('/')
    return render_template("register.html")

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template("dashboard.html")

# Add Note
@app.route('/addnote', methods=['GET','POST'])
def addnote():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        cursor.execute(
            "INSERT INTO notes(user_id,title,content) VALUES(%s,%s,%s)",
            (session['user'], title, content)
        )
        db.commit()

        return redirect('/viewnotes')

    return render_template("addnote.html")

# View Notes
@app.route('/viewnotes')
def viewnotes():
    if 'user' not in session:
        return redirect('/')
    cursor.execute("SELECT * FROM notes WHERE user_id=%s ORDER BY pinned DESC, created_at DESC",(session['user'],))
    notes = cursor.fetchall()
    return render_template("viewnotes.html", notes=notes)

# View Single Note
@app.route('/note/<int:id>')
def single_note(id):
    if 'user' not in session:
        return redirect('/')
    cursor.execute("SELECT * FROM notes WHERE id=%s AND user_id=%s", (id, session['user']))
    note = cursor.fetchone()
    return render_template("singlenote.html", note=note)

@app.route('/profile', methods=['GET','POST'])
def profile():

    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':

        file = request.files['photo']

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            cursor.execute(
                "UPDATE users SET profile_pic=%s WHERE id=%s",
                (filename, session['user'])
            )
            db.commit()

    cursor.execute(
        "SELECT username,email,profile_pic FROM users WHERE id=%s",
        (session['user'],)
    )

    user = cursor.fetchone()

    return render_template("profile.html", user=user)

@app.route('/pin/<int:id>')
def pin_note(id):

    if 'user' not in session:
        return redirect('/')

    cursor.execute("SELECT pinned FROM notes WHERE id=%s",(id,))
    note = cursor.fetchone()

    new_status = 0 if note[0] == 1 else 1

    cursor.execute(
        "UPDATE notes SET pinned=%s WHERE id=%s AND user_id=%s",
        (new_status, id, session['user'])
    )

    db.commit()

    return redirect('/viewnotes')

# Delete Note
@app.route('/delete/<int:id>')
def delete_note(id):
    if 'user' not in session:
        return redirect('/')
    cursor.execute("DELETE FROM notes WHERE id=%s AND user_id=%s", (id, session['user']))
    db.commit()
    return redirect('/viewnotes')

@app.route('/update/<int:id>', methods=['GET','POST'])
def update_note(id):

    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        cursor.execute(
            "UPDATE notes SET title=%s, content=%s WHERE id=%s AND user_id=%s",
            (title, content, id, session['user'])
        )

        db.commit()
        return redirect('/viewnotes')

    cursor.execute(
        "SELECT * FROM notes WHERE id=%s AND user_id=%s",
        (id, session['user'])
    )

    note = cursor.fetchone()

    return render_template("updatenote.html", note=note)


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact', methods=['GET','POST'])
def contact():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Mail to Admin
        admin_msg = Message(
            subject="New Contact Message",
            sender=app.config['MAIL_USERNAME'],
            recipients=['yourgmail@gmail.com']
        )

        admin_msg.body = f"""
Name: {name}
Email: {email}

Message:
{message}
"""

        mail.send(admin_msg)


        # Confirmation Mail to User
        user_msg = Message(
            subject="Thank you for contacting us",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )

        user_msg.body = f"""
Hello {name},

Thank you for contacting the Notes Management System.

We have received your message successfully.
Our team will review it and reach out to you soon.

Best Regards,
Notes Management System Team
"""

        mail.send(user_msg)

        return render_template("contact.html", success="Message sent successfully!")

    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)