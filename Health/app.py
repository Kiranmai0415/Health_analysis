from flask import Flask, render_template, request, redirect, session, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'health123'

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345@Code'  # change this
app.config['MYSQL_DB'] = 'health_db'

mysql = MySQL(app)

# Login route
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                    (username, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password!'

    return render_template('login.html', error=error)

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)