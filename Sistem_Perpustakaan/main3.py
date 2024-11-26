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
app.config['MYSQL_DB'] = 'perpus'

# Intialize MySQL
mysql = MySQL(app)

# http://localhost:5000  the following will be our login page, which will use both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def login():  
    # Output message if something goes wrong...
    msg = ''
    # Check if "id staff" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'idstaff' in request.form and 'password' in request.form:
        # Create variables for easy access
        idstaff = request.form['idstaff']
        password = request.form['password']
        
        # Retrieve the hashed password
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM staff WHERE id_staff = %s AND password = %s', (idstaff, password,))
        # Fetch one record and return the result
        akun = cursor.fetchone()
        # If akun exists in login table in out database
        if akun:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id_staff'] = akun['id_staff']
            session['nama_staff'] = akun['nama_staff']  
                      
            # Redirect to home page  
            return render_template('menu1.html', nama_staff=session['nama_staff'], id_staff=session['id_staff'])
        else:
            # Akun doesnt exist or username/password incorrect
            msg = ('Incorrect ID/password!')
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)

# http://localhost:5000/login1  the following will be our login page, which will use both GET and POST requests
@app.route('/login1', methods=['GET', 'POST'])
def login1():  
    # Output message if something goes wrong...
    msg = ''
    # Check if "id anggota" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'idanggota' in request.form and 'password' in request.form:
        # Create variables for easy access
        idanggota = request.form['idanggota']
        password = request.form['password']
        
        # Retrieve the hashed password
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM anggota WHERE id_anggota = %s AND password = %s', (idanggota, password,))
        # Fetch one record and return the result
        akun = cursor.fetchone()
        # If akun exists in login table in out database
        if akun:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id_anggota'] = akun['id_anggota']
            session['nama_anggota'] = akun['nama_anggota']  
                      
            # Redirect to home page  
            return render_template('menu2.html', nama_anggota=session['nama_staff'], id_staff=session['id_anggota'])
        else:
            # Akun doesnt exist or username/password incorrect
            msg = ('Incorrect ID/password!')
    # Show the login form with message (if any)
    return render_template('index.html', msg=msg)


# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    #session.pop('id', None)
    session.pop('idstaff', None)   
    session.pop('nmstaff', None)   
     
    # Redirect to login page
    #return redirect(url_for('login'))

    return render_template('index.html')

# http://localhost:5000/login/staff - this will be the registration page, we need to use both GET and POST requests
@app.route('/registrasi', methods=['GET', 'POST'])
def registrasi():
    # Output message if something goes wrong...
    msg = ''
    # Check if "id staff", "nama staff", "no. telp staff", "email" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'idstaff' in request.form and 'nmstaff' in request.form and 'tlpstaff' in request.form and 'shift' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        idstaff = request.form['idstaff']
        nmstaff = request.form['nmstaff']
        tlpstaff = request.form['tlpstaff']
        email = request.form['email']
        shift = request.form['shift']        
        password = request.form['password']        
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM staff WHERE id_staff = %s', (idstaff,))
        akun = cursor.fetchone()
        # If akun exists show error and validation checks
        if akun:
            msg = 'Account already exists!'
        elif not re.match(r'[A-Za-z0-9]+', idstaff):
            msg = 'ID Staff must contain only characters and numbers!'
        elif not re.match(r'[a-zA-Z]+', nmstaff):
            msg = 'Invalid nama staff!'    
        elif not re.match(r'[z0-9]+', tlpstaff):
            msg = 'Invalid nomor telepon!'     
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'        
        elif not idstaff or not nmstaff or not tlpstaff or not email or not password :
            msg = 'Please fill out the form!'
        else:
            # Hash the password
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
            # Akun doesn't exist, and the form data is valid, so insert the new account into the accounts table
            cursor.execute('INSERT INTO staff VALUES (%s, %s, %s, %s, %s, %s)', (idstaff, nmstaff, tlpstaff, email, shift, password))
            mysql.connection.commit()
            msg = 'User baru telah berhasil ditambahkan!'

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show staff form with message (if any)
    return render_template('registrasi.html', msg=msg)

# http://localhost:5000/login/registrasi1 - this will be the registration page, we need to use both GET and POST requests
@app.route('/registrasi1', methods=['GET', 'POST'])
def registrasi1():
    # Output message if something goes wrong...
    msg = ''
    # Check if "id anggota", "nama anggota", "no. telp anggota", "email" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'idanggota' in request.form and 'nmanggota' in request.form and 'tlpanggota' in request.form and 'email' in request.form and 'password' in request.form :
        # Create variables for easy access
        idanggota = request.form['idanggota']
        nmanggota = request.form['nmanggota']
        tlpanggota = request.form['tlpanggota']
        email = request.form['email']
        password = request.form['password']        
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM anggota WHERE id_anggota = %s', (idanggota,))
        akun = cursor.fetchone()
        # If akun exists show error and validation checks
        if akun:
            msg = 'Account already exists!'
        elif not re.match(r'[A-Za-z0-9]+', idanggota):
            msg = 'ID Staff must contain only characters and numbers!'
        elif not re.match(r'[a-zA-Z]+', nmanggota):
            msg = 'Invalid nama staff!'    
        elif not re.match(r'[z0-9]+', tlpanggota):
            msg = 'Invalid nomor telepon!'     
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'        
        elif not idanggota or not nmanggota or not tlpanggota or not email or not password :
            msg = 'Please fill out the form!'
        else:
            # Hash the password
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
            # Akun doesn't exist, and the form data is valid, so insert the new account into the accounts table
            cursor.execute('INSERT INTO anggota VALUES (%s, %s, %s, %s, %s)', (idanggota, nmanggota, tlpanggota, email, password))
            mysql.connection.commit()
            msg = 'User baru telah berhasil ditambahkan!'

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show staff form with message (if any)
    return render_template('registrasi1.html', msg=msg)

# http://localhost:5000/home - this will be the home page, only accessible for logged in users
@app.route('/home')
def home():
    # Check if the user is logged in
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', nama_staff=session['nama_staff'], id_staff=session['id_staff'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/menu1 - this will be the home page, only accessible for logged in users
@app.route('/menu1')
def menu1():
    # Check if the user is logged in
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('menu1.html', nama_staff=session['nama_staff'], id_staff=session['id_staff'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

# http://localhost:5000/menu2 - this will be the home page, only accessible for logged in users
@app.route('/menu2')
def menu2():
    # Check if the user is logged in
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('menu2.html', nama_anggota=session['nama_anggota'], id_anggota=session['id_anggota'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


# http://localhost:5000/browsestaff - this will be the home page, only accessible for logged in users
@app.route('/browsestaff') 
def browsestaff(): 
    # Check if the user is logged in
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM staff") 
        #cursor.execute('SELECT * FROM staff WHERE id_staff = %s', (session['id_staff'],))
        akunstaff = cursor.fetchall()   
        cursor.close()        
        return render_template('browsestaff.html', akunstaff=akunstaff) 
    # User is not logged in redirect to login page
    return redirect(url_for('menu1'))

# http://localhost:5000/browseanggota - this will be the home page, only accessible for logged in users
@app.route('/browseanggota') 
def browseanggota(): 
    # Check if the user is logged in
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM anggota")        
        akunanggota = cursor.fetchall()   
        cursor.close()        
        return render_template('browseanggota.html', akunanggota=akunanggota) 
    # User is not logged in redirect to login page
    return redirect(url_for('menu2'))

# http://localhost:5000/profile - this will be the profile page, only accessible for logged in users
@app.route('/profile')
def profile():
    # Check if the user is logged in
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM staff WHERE id_staff = %s', (session['id_staff'],))
        akun= cursor.fetchone()
        # Show the profile page with account info        
        return render_template('profile.html', account=akun)
    # User is not logged in redirect to login page
    return redirect(url_for('menu1'))

# http://localhost:5000/editstaff - this will be the home page, only accessible for logged in users
#@app.route('/editstaff/<int:id_staff>', methods=['GET', 'POST'])
#def editstaff(id_staff):
    
    # Fetch the staff member using id_staff
    staff_member = get_staff_member(id_staff)  # Your function to get the staff member
    
    if request.method == 'POST':
        # Handle form submission for editing
        # Update staff member details here
        pass
    
    return render_template('edit_staff.html', staff_member=staff_member)
@app.route('/editstaff')
def editstaff():
    # Check if the user is logged in
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM staff")         
        akunstaff = cursor.fetchall()   
        cursor.close()        
        return render_template('editstaff.html', akunstaff=akunstaff) 
    # User is not logged in redirect to login page
    return redirect(url_for('menu1'))

# http://localhost:5000/gantipwd - this will be the logout page
@app.route('/gantipwd')
def gantipwd():
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM staff WHERE id_staff = %s', (session['id_staff'],))
        #cursor.execute('SELECT * FROM staff WHERE id_staff = %s AND password = %s', (idstaff, password,))
        akun= cursor.fetchone()
        # Show the profile page with account info        
        return render_template('gantipwd.html', account=akun)
    # Output message if something goes wrong...
    msg = ''
    # Check if "id staff", and change the password
    if request.method == 'POST' and 'passwordlama' in request.form and 'passwordbaru' in request.form :
        # Create variables for easy access
        idstaff = request.form['idstaff']           
        passwordbaru = request.form['passwordbaru']        
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM staff WHERE id_staff = %s', (idstaff,))
        akun = cursor.fetchone()
        # If akun exists show error and validation checks
        if akun:
            #msg = 'Account already exists!'
            # Hash the password
            hash = passwordbaru + app.secret_key
            hash = hashlib.sha1(hash.encode())
            passwordbaru = hash.hexdigest()
            
            execute('REPLACE INTO staff (PASSWORD) VALUES (%s,)', (passwordbaru))
            mysql.connection.commit()
            msg = 'PASSWORD telah berhasil ditambahkan!'
        else:
            # Akun doesnt exist or username/password incorrect
            msg = ('Incorrect ID/password!')    
    # User is not logged in redirect to login page
    return redirect(url_for('home'))

# http://localhost:5000/buku - this will be the logout page
@app.route('/buku')
def buku():
    return redirect(url_for('home'))

# http://localhost:5000/anggota - this will be the logout page
@app.route('/anggota')
def anggota():
    return redirect(url_for('home'))

# http://localhost:5000/peminjaman - this will be the logout page
@app.route('/peminjaman')
def peminjaman():
    return redirect(url_for('home'))

# http://localhost:5000/pengembalian - this will be the logout page
@app.route('/pengembalian')
def pengembalian():
    return redirect(url_for('home'))

if __name__ == '__main__':
  app.run()