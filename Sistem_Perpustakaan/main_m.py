from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import MySQLdb.cursors, re, hashlib

app = Flask(__name__)

# Change this to your secret key (it can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_login'

# Intialize MySQL
mysql = MySQL(app)

# http://localhost:5000  the following will be our login page, which will use both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def login():  
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        
        # Retrieve the hashed password
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM login WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return the result
        akun = cursor.fetchone()
        # If akun exists in login table in out database
        if akun:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = akun['id']
            session['username'] = akun['username']  
                      
            # Redirect to home page            
            return render_template('home.html', username=session['username'])
            #return 'Login berhasil!'
        else:
            # Akun doesnt exist or username/password incorrect
            msg = ('Incorrect username/password!')
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)

# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)   
     
    # Redirect to login page
    #return redirect(url_for('login'))

    return render_template('index.html')

# http://localhost:5000/login/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/registrasi', methods=['GET', 'POST'])
def registrasi():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM login WHERE username = %s', (username,))
        akun = cursor.fetchone()
        # If akun exists show error and validation checks
        if akun:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Hash the password
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
            # Akun doesn't exist, and the form data is valid, so insert the new account into the accounts table
            cursor.execute('INSERT INTO login VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'User baru telah berhasil ditambahkan!'

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('registrasi.html', msg=msg)

# http://localhost:5000/home - this will be the home page, only accessible for logged in users
@app.route('/home')
def home():
    # Check if the user is logged in
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/profile - this will be the profile page, only accessible for logged in users
@app.route('/profile')
def profile():
    # Check if the user is logged in
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM login WHERE id = %s', (session['id'],))
        akun= cursor.fetchone()
        # Show the profile page with account info        
        return render_template('profile.html', account=akun)
    # User is not logged in redirect to login page
    return redirect(url_for('login'))

if __name__ == '__main__':
  app.run()