from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from flask import jsonify
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
    msg = ''
    reminders = []
    if request.method == 'POST' and 'idanggota' in request.form and 'password' in request.form:
        idanggota = request.form['idanggota']
        password = request.form['password']
        
        # Hash the password
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM anggota WHERE id_anggota = %s AND password = %s', (idanggota, password,))
        akun = cursor.fetchone()
        
        if akun:
            session['loggedin'] = True
            session['id_anggota'] = akun['id_anggota']
            session['nama_anggota'] = akun['nama_anggota']  
            
            cursor.execute('''
                SELECT 
                    peminjaman.id_pinjam,
                    peminjaman.tanggal_pinjam,
                    peminjaman.id_buku,  
                    peminjaman.id_staff,                                 
                    buku.judul_buku,
                    staffreminder.id_staff,
                    staffreminder.tgl_reminder,
                    staffreminder.remarks                                        
                FROM 
                    peminjaman 
                JOIN 
                    buku ON peminjaman.id_buku = buku.id_buku
                LEFT JOIN 
                    staffreminder ON peminjaman.id_pinjam = staffreminder.id_pinjam
                WHERE    
                    peminjaman.id_anggota = %s
            ''', (idanggota,))
            akunpeminjaman = cursor.fetchall()              
            
            # Calculate Tanggal Kembali
            for pinjam in akunpeminjaman:
                current_date = datetime.now()                
                tanggal_pinjam = pinjam['tanggal_pinjam']
                if isinstance(tanggal_pinjam, str):  
                    tanggal_pinjam = datetime.strptime(tanggal_pinjam, '%Y-%m-%d')
                pinjam['tanggal_kembali'] = tanggal_pinjam + timedelta(days=7)
                if isinstance(pinjam['tanggal_pinjam'], str):
                    pinjam['tanggal_pinjam'] = datetime.strptime(pinjam['tanggal_pinjam'], '%Y-%m-%d')  
                tanggal_kembali = pinjam['tanggal_kembali']  # Assuming this is also a datetime object
               
                if isinstance(pinjam['tgl_reminder'], str):
                    # Convert tgl_reminder from varchar to datetime using the correct format
                    pinjam['tgl_reminder'] = datetime.strptime(pinjam['tgl_reminder'], '%Y-%m-%d')  # Correct format
                                    
                # Cek reminder tanggal kembali
                # Reminder logic
                if current_date <= tanggal_kembali + timedelta(days=2):                    
                    if current_date.date() == tanggal_kembali.date():  # Due today
                        reminders.append(f"JANGAN LUPA! buku '{pinjam['judul_buku']}' harus balik hari ini. Jangan melebihi batas pengembalian buku pukul 2:00 siang. Terima kasih.")
                    elif current_date.date() == (tanggal_kembali - timedelta(days=1)).date():  # Due tomorrow
                        reminders.append(f"Perhatian, buku '{pinjam['judul_buku']}' harus balik besok. Terima kasih.")
                    elif current_date.date() == (tanggal_kembali - timedelta(days=2)).date():  # Due in 2 days
                        reminders.append(f"Perhatian, buku '{pinjam['judul_buku']}' harus balik dalam 2 hari kedepan. Terima kasih.")
                else:
                    if current_date > tanggal_kembali:  # Overdue check
                        overdue_days = (current_date - tanggal_kembali).days
                        reminders.append(f"Perhatian, buku '{pinjam['judul_buku']}' sudah melewati batas pinjam dan terkena denda Rp. 1000/Hari!<br>Anda sudah lewat {overdue_days} hari dari tanggal pengembalian.<br>")
                                               
            return render_template('home.html', 
                                   nama_anggota=session['nama_anggota'], 
                                   akunpeminjaman=akunpeminjaman,                                   
                                   reminders=reminders, 
                                   id_anggota=session['id_anggota'])
        else:
            # Akun doesnt exist or username/password incorrect
            msg = ('Incorrect ID/password!')    
            
    return render_template('index.html', msg=msg)

# http://localhost:5000/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('id_anggota', None)
    session.pop('nama_anggota', None)
    session.pop('id_staff', None)   
    session.pop('nama_staff', None)
    session.pop('no_telp_staff', None)   
    session.pop('email_staff', None)
    session.pop('shift_kerja', None)   
         
    # Redirect to login page
    return render_template('index.html')

# http://localhost:5000/login/registasi - this will be the registration page, we need to use both GET and POST requests
from flask import session
@app.route('/registrasi', methods=['GET', 'POST'])
def registrasi():
    msg = ''
    new_id_anggota = None  # Initialize variable for new ID

    if request.method == 'GET':
        # Handle the first visit to the registrasi page (GET request)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Fetch the last used id_anggota from the database
        cursor.execute('SELECT id_anggota FROM anggota ORDER BY id_anggota DESC LIMIT 1;')
        last_idAnggota = cursor.fetchone()

        if last_idAnggota:
            # If there are existing entries, generate the next id_anggota
            current_id = last_idAnggota['id_anggota']  # Use the dictionary key for id_anggota
            new_id_number = int(current_id[3:]) + 1  # Assuming ID format "ANGxxx"
            new_id_anggota = f"ANG{new_id_number:03}"
        else:
            # If no entries exist, start from "ANG001"
            new_id_anggota = "ANG001"
        
        # Store the generated id in session
        session['new_id_anggota'] = new_id_anggota

    if request.method == 'POST':
        # Handle form submission (POST request)
        new_id_anggota = session.get('new_id_anggota')  # Retrieve the stored ID from session
        nmanggota = request.form['nmanggota']
        tlpanggota = request.form['tlpanggota']
        email = request.form['email']
        password = request.form['password']

        # Check if new_id_anggota exists in session
        if new_id_anggota is None:
            msg = "ID Anggota is not generated correctly!"
            return render_template('registrasi.html', new_id_anggota=new_id_anggota, msg=msg)
        
        # Debugging print statement to see the new_id_anggota value
        print("New ID Anggota:", new_id_anggota)  # This will print to your terminal/console
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check if the phone number already exists
        cursor.execute('SELECT * FROM anggota WHERE no_telp_anggota = %s', (tlpanggota,))
        akun_tlp = cursor.fetchone()

        # Check if the email already exists
        cursor.execute('SELECT * FROM anggota WHERE email_anggota = %s', (email,))
        akun_email = cursor.fetchone()

        if akun_tlp:
            msg = 'Account already exists with this phone number!'
        elif akun_email:
            msg = 'Account already exists with this email address!'        
        elif not re.match(r'[a-zA-Z]+', nmanggota):
            msg = 'Invalid nama staff!'    
        elif not re.match(r'^[0-9]+$', tlpanggota):  # Only numbers for phone number
            msg = 'Invalid nomor telepon!'     
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'        
        elif not nmanggota or not tlpanggota or not email or not password:
            msg = 'Please fill out the form!'
        else:
            # Hash password before storing it
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
            
            # Insert new member into the database, using the generated new_id_anggota
            cursor.execute('INSERT INTO anggota (id_anggota, nama_anggota, no_telp_anggota, email_anggota, password) VALUES (%s, %s, %s, %s, %s)', 
                           (new_id_anggota, nmanggota, tlpanggota, email, password))
            mysql.connection.commit()

            msg = 'User baru telah berhasil ditambahkan!'

            # After successfully adding, generate the next ID for the next registration
            cursor.execute('SELECT id_anggota FROM anggota ORDER BY id_anggota DESC LIMIT 1;')
            last_idAnggota = cursor.fetchone()
            if last_idAnggota:
                current_id = last_idAnggota['id_anggota']  # Use the dictionary key for id_anggota
                new_id_number = int(current_id[3:]) + 1
                new_id_anggota = f"ANG{new_id_number:03}"
                
            # Store the new ID in session for the next registration
            session['new_id_anggota'] = new_id_anggota

    # Render the registration page with the next available new_id_anggota
    return render_template('registrasi.html', new_id_anggota=new_id_anggota, msg=msg)


# http://localhost:5000/home - this will be the home page, only accessible for logged in users
@app.route('/home')
def home():
    # Check if the user is logged in
    if 'loggedin' in session:
        idanggota = session['id_anggota']
        akunpeminjaman = session.get('akunpeminjaman', [])        
        reminders = session.get('reminders', [])
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT 
                    peminjaman.id_pinjam,
                    peminjaman.tanggal_pinjam,
                    peminjaman.id_buku,  
                    peminjaman.id_staff,                                 
                    buku.judul_buku,
                    staffreminder.id_staff,
                    staffreminder.tgl_reminder,
                    staffreminder.remarks                    
                FROM 
                    peminjaman 
                JOIN 
                    buku ON peminjaman.id_buku = buku.id_buku
                LEFT JOIN 
                    staffreminder ON peminjaman.id_pinjam = staffreminder.id_pinjam
                WHERE    
                    peminjaman.id_anggota = %s
        ''', (idanggota,))
        akunpeminjaman = cursor.fetchall()
            
        # Calculate Tanggal Kembali
        for pinjam in akunpeminjaman:
            current_date = datetime.now()                
            tanggal_pinjam = pinjam['tanggal_pinjam']
            if isinstance(tanggal_pinjam, str):  
                tanggal_pinjam = datetime.strptime(tanggal_pinjam, '%Y-%m-%d')
            pinjam['tanggal_kembali'] = tanggal_pinjam + timedelta(days=7)
            if isinstance(pinjam['tanggal_pinjam'], str):
                pinjam['tanggal_pinjam'] = datetime.strptime(pinjam['tanggal_pinjam'], '%Y-%m-%d')  
            tanggal_kembali = pinjam['tanggal_kembali']  # Assuming this is also a datetime object            
            
            if isinstance(pinjam['tgl_reminder'], str):
                # Convert tgl_reminder from varchar to datetime using the correct format
                pinjam['tgl_reminder'] = datetime.strptime(pinjam['tgl_reminder'], '%Y-%m-%d')  # Correct format
                            
            # Cek reminder tanggal kembali
            # Reminder logic
            if current_date <= tanggal_kembali + timedelta(days=2):                    
                if current_date.date() == tanggal_kembali.date():  # Due today
                    reminders.append(f"JANGAN LUPA! buku '{pinjam['judul_buku']}' harus balik hari ini. Jangan melebihi batas pengembalian buku pukul 2:00 siang. Terima kasih.")
                elif current_date.date() == (tanggal_kembali - timedelta(days=1)).date():  # Due tomorrow
                    reminders.append(f"Perhatian, buku '{pinjam['judul_buku']}' harus balik besok. Terima kasih.")
                elif current_date.date() == (tanggal_kembali - timedelta(days=2)).date():  # Due in 2 days
                    reminders.append(f"Perhatian, buku '{pinjam['judul_buku']}' harus balik dalam 2 hari kedepan. Terima kasih.")
            else:
                if current_date > tanggal_kembali:  # Overdue check
                    overdue_days = (current_date - tanggal_kembali).days
                    reminders.append(f"Perhatian, buku '{pinjam['judul_buku']}' sudah melewati batas pinjam dan terkena denda Rp. 1000/Hari!<br>Anda sudah lewat {overdue_days} hari dari tanggal pengembalian.<br>")
                                
        return render_template('home.html', 
                                nama_anggota=session['nama_anggota'], 
                                akunpeminjaman=akunpeminjaman,                                   
                                reminders=reminders, 
                                id_anggota=session['id_anggota'])       

    # If not logged in, redirect to login or show an appropriate message
    return redirect(url_for('login'))


# http://localhost:5000/profile - this will be the profile page, only accessible for logged in users
@app.route('/profile')
def profile():
    # Check if the user is logged in
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM anggota WHERE id_anggota = %s', (session['id_anggota'],))
        akun= cursor.fetchone()
        # Show the profile page with account info        
        return render_template('profile.html', account=akun)
    # User is not logged in redirect to login page
    return redirect(url_for('login'))

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
    return redirect(url_for('home'))

# http://localhost:5000  the following will be our login page, which will use both GET and POST requests
@app.route('/chpwd', methods=['GET', 'POST'])
def chpwd():  
    # Check if the user is logged in
    if 'loggedin' in session:
        # Output message if something goes wrong...
        msg = ''
        # Change "password" POST requests exist (user submitted form)
        if request.method == 'POST' and 'passwordbr' in request.form:
            # Create variables for easy access
            id_anggota=session['id_anggota']
            passwordbr = request.form['passwordbr']
            passwordbr1 = request.form['passwordbr1']        
            
            if passwordbr != passwordbr1:
                msg = ('Password tidak sama!, Harap diulang')
                return render_template('chpwd.html', id_anggota=session['id_anggota'], nama_anggota=session['nama_anggota'], msg=msg)
            
            # Retrieve the hashed password
            hash = passwordbr + app.secret_key
            hash = hashlib.sha1(hash.encode())
            passwordbr = hash.hexdigest()
        
            # Check if account exists using MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM anggota WHERE id_anggota = %s', (session['id_anggota'],))
            # Fetch one record and return the result
            akun = cursor.fetchone()
            # If akun exists in login table in out database
            if akun:
                # update data password          
                # Update query
                cursor.execute('UPDATE anggota SET password = %s WHERE id_anggota = %s', (passwordbr, id_anggota))
                mysql.connection.commit()            
                # Redirect to home page            
                return render_template('home.html', id_anggota=session['id_anggota'], nama_anggota=session['nama_anggota'])
                       
            else:
                # Akun doesnt exist or username/password incorrect
             msg = ('Id Anggota tidak ada!')
        # Show the login form with message (if any)
        return render_template('chpwd.html', id_anggota=session['id_anggota'], nama_anggota=session['nama_anggota'], msg=msg)

# http://localhost:5000/edtanggota  the following will be our login page, which will use both GET and POST requests
@app.route('/edtanggota', methods=['GET', 'POST'])
def edtanggota():
    # Check if the user is logged in
    if 'loggedin' in session:
        msg = ''
        
        if request.method == 'POST' and 'nmanggota' in request.form and 'tlpanggota' in request.form and 'email' in request.form:
            # Extract form values
            nmanggota = request.form['nmanggota']
            tlpanggota = request.form['tlpanggota']
            email = request.form['email']
            
            # Get the id_anggota from session
            id_anggota = session.get('id_anggota')

            # If id_anggota is not in session, redirect to login
            if not id_anggota:
                msg = 'Session expired or you are not logged in.'
                return redirect('/login')  # Or render the login page

            # Update the account in the database
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM anggota WHERE id_anggota = %s', (id_anggota,))
            akun = cursor.fetchone()

            if akun:
                # Update the account details
                cursor.execute('UPDATE anggota SET nama_anggota = %s, no_telp_anggota = %s, email_anggota = %s WHERE id_anggota = %s', 
                               (nmanggota, tlpanggota, email, id_anggota))
                mysql.connection.commit()
                msg = 'Account updated successfully!'
                return render_template('home.html', msg=msg, id_anggota=id_anggota, nama_anggota=nmanggota)
            else:
                msg = 'Account not found!'
        
        # Handle the GET request and fetch the user's current data
        else:
            id_anggota = session.get('id_anggota')

            if not id_anggota:
                msg = 'Session expired or you are not logged in.'
                return redirect('/login')

            # Fetch the user's data from the database
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM anggota WHERE id_anggota = %s', (id_anggota,))
            akun = cursor.fetchone()

            if akun:
                # Populate session variables for easy access
                session['nama_anggota'] = akun['nama_anggota']
                session['no_telp_anggota'] = akun['no_telp_anggota']
                session['email_anggota'] = akun['email_anggota']
                
                # Pass values to the template
                return render_template('edtanggota.html', 
                                       id_anggota=akun['id_anggota'],
                                       nama_anggota=akun['nama_anggota'],
                                       no_telp_anggota=akun['no_telp_anggota'],
                                       email_anggota=akun['email_anggota'],
                                       msg=msg)
            else:
                msg = 'Account not found!'
                return render_template('home.html', msg=msg)

    else:
        return redirect('/home')  # Redirect to login page if not logged in


# http://localhost:5000/loginstaff  the following will be our login page, which will use both GET and POST requests
@app.route('/loginstaff', methods=['GET', 'POST'])
def loginstaff():  
    # Get date today
    from datetime import date 
    current_date = date.today().strftime('%d %B %Y')  # Format: "DD MMMMM YYYY" 
    hari_ini = date.today().strftime('%Y-%m-%d')  # Format: "YYYY-MM-DD"    
    
    # Output message if something goes wrong...
    msg = ''
    
    # Check if the staff table has records (if empty, redirect to registration)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT COUNT(*) as count FROM staff')
    staff_count = cursor.fetchone()['count']
    
    # If there are no staff records, redirect to registrasistaff
    if staff_count == 0:
        # Registrasi Staff admin yang pertama kali
        return redirect(url_for('firstregistrasistaff'))
    
    else:
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
            # If akun exists in the staff table
            if akun:
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id_staff'] = akun['id_staff']
                session['nama_staff'] = akun['nama_staff']  
                session['no_telp_staff'] = akun['no_telp_staff'] 
                session['email_staff'] = akun['email_staff']              
                session['shift_kerja'] = akun['shift_kerja'] 
                none=""
                
                # Check peminjaman has been confirmed
                cursor.execute("SELECT COUNT(*) FROM peminjaman WHERE id_staff IS NOT NULL")
                # Fetch the result
                bukuYangMasihDiPinjam = cursor.fetchone()                
                # If exists is None or the count is 0
                if bukuYangMasihDiPinjam is None or bukuYangMasihDiPinjam['COUNT(*)'] == 0:
                    bukuYangMasihDiPinjam = 'Tidak ada.'
                else:
                    bukuYangMasihDiPinjam = bukuYangMasihDiPinjam['COUNT(*)']  # The count value
                    
                # Check if peminjaman has been late (tanggal_pinjam is more than 7 days ago)
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM peminjaman 
                    WHERE id_staff IS NOT NULL 
                    AND tanggal_pinjam <= %s
                    AND tanggal_pinjam + INTERVAL 7 DAY < %s
                """, (hari_ini, hari_ini))
                # Fetch the result
                bukuYangMasihTerlambatBalik = cursor.fetchone()
                # Handle the result
                if bukuYangMasihTerlambatBalik is None or bukuYangMasihTerlambatBalik['COUNT(*)'] == 0:
                    bukuYangTerlambat = 'Tidak ada.'
                else:
                    bukuYangTerlambat = bukuYangMasihTerlambatBalik['COUNT(*)']  # The count of overdue books
                
                # Check peminjaman to confirm
                cursor.execute("SELECT COUNT(*) FROM peminjaman WHERE tanggal_pinjam = %s AND id_staff = %s", (hari_ini, none))
                # Fetch the result
                existsPeminjaman = cursor.fetchone()                
                # If exists is None or the count is 0
                if existsPeminjaman is None or existsPeminjaman['COUNT(*)'] == 0:
                    hasilPeminjaman = 'Tidak ada.'
                else:
                    hasilPeminjaman = existsPeminjaman['COUNT(*)']  # The count value
                
                # Check pengembalian today to comfirm
                cursor.execute("SELECT COUNT(*) FROM pengembalian WHERE tanggal_kembali = %s AND id_staff = %s", (hari_ini, none))
                # Fetch the result
                existsPengembalian = cursor.fetchone()  
                
                # If exists is None or the count is 0
                if existsPengembalian is None or existsPengembalian['COUNT(*)'] == 0:
                    hasilPengembalian = 'Tidak ada.'
                else:
                    hasilPengembalian = existsPengembalian['COUNT(*)']  # The count value
                    
                # Query to check books that are due to be returned today
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM peminjaman 
                    WHERE tanggal_pinjam + INTERVAL 7 DAY = %s
                    AND id_staff IS NOT NULL
                """, (hari_ini,))
                # Fetch the result
                bukuYangKembaliHariIni = cursor.fetchone()
               
                # Handle the result
                if bukuYangKembaliHariIni is None or bukuYangKembaliHariIni['COUNT(*)'] == 0:
                    bukuYangHarusKembali = 'Tidak ada.'
                else:
                    bukuYangHarusKembali = bukuYangKembaliHariIni['COUNT(*)']  # The count of books returned today
             
                # Redirect to home page  
                return render_template('homestaff.html', current_date=current_date, 
                                       bukuYangMasihDiPinjam=bukuYangMasihDiPinjam,
                                       bukuYangHarusKembali=bukuYangHarusKembali,
                                       bukuYangTerlambat=bukuYangTerlambat,
                                       hasilPeminjaman=hasilPeminjaman, 
                                       hasilPengembalian=hasilPengembalian, 
                                       nama_staff=session['nama_staff'], id_staff=session['id_staff'])
            else:
                # Account doesn't exist or username/password incorrect
                msg = 'Incorrect ID/password!'
    
    # Show the login form with message (if any)
    return render_template('loginstaff.html', msg=msg)


# http://localhost:5000/homestaff - this will be the home page, only accessible for logged in users
@app.route('/homestaff')
def homestaff():   
    # Get date today
    from datetime import date 
    current_date = date.today().strftime('%d %B %Y')  # Format: "DD MMMMM YYYY" 
    hari_ini = date.today().strftime('%Y-%m-%d')  # Format: "YYYY-MM-DD"   
    none=""
    
    # Check if the user is logged in
    if 'loggedin' in session:
        # User is loggedin show them the home page
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Check peminjaman has been confirmed
        cursor.execute("SELECT COUNT(*) FROM peminjaman WHERE id_staff IS NOT NULL")
        # Fetch the result
        bukuYangMasihDiPinjam = cursor.fetchone()                
        # If exists is None or the count is 0
        if bukuYangMasihDiPinjam is None or bukuYangMasihDiPinjam['COUNT(*)'] == 0:
            bukuYangMasihDiPinjam = 'Tidak ada.'
        else:
            bukuYangMasihDiPinjam = bukuYangMasihDiPinjam['COUNT(*)']  # The count value
            
        # Check if peminjaman has been late (tanggal_pinjam is more than 7 days ago)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM peminjaman 
            WHERE id_staff IS NOT NULL 
            AND tanggal_pinjam <= %s
            AND tanggal_pinjam + INTERVAL 7 DAY < %s
        """, (hari_ini, hari_ini))
        # Fetch the result
        bukuYangMasihTerlambatBalik = cursor.fetchone()
        # Handle the result
        if bukuYangMasihTerlambatBalik is None or bukuYangMasihTerlambatBalik['COUNT(*)'] == 0:
            bukuYangTerlambat = 'Tidak ada.'
        else:
            bukuYangTerlambat = bukuYangMasihTerlambatBalik['COUNT(*)']  # The count of overdue books
        
        # Check peminjaman to confirm
        cursor.execute("SELECT COUNT(*) FROM peminjaman WHERE tanggal_pinjam = %s AND id_staff = %s", (hari_ini, none))
        # Fetch the result
        existsPeminjaman = cursor.fetchone()                
        # If exists is None or the count is 0
        if existsPeminjaman is None or existsPeminjaman['COUNT(*)'] == 0:
            hasilPeminjaman = 'Tidak ada.'
        else:
            hasilPeminjaman = existsPeminjaman['COUNT(*)']  # The count value
        
        # Check pengembalian today to comfirm
        cursor.execute("SELECT COUNT(*) FROM pengembalian WHERE tanggal_kembali = %s AND id_staff = %s", (hari_ini, none))
        # Fetch the result
        existsPengembalian = cursor.fetchone()  
                          
        # If exists is None or the count is 0
        if existsPengembalian is None or existsPengembalian['COUNT(*)'] == 0:
            hasilPengembalian = 'Tidak ada.'
        else:
            hasilPengembalian = existsPengembalian['COUNT(*)']  # The count value

        # Query to check books that are due to be returned today
        cursor.execute("""
            SELECT COUNT(*) 
            FROM peminjaman 
            WHERE tanggal_pinjam + INTERVAL 7 DAY = %s
            AND id_staff IS NOT NULL
        """, (hari_ini,))
        # Fetch the result
        bukuYangKembaliHariIni = cursor.fetchone()
        # Handle the result
        if bukuYangKembaliHariIni is None or bukuYangKembaliHariIni['COUNT(*)'] == 0:
            bukuYangHarusKembali = 'Tidak ada.'
        else:
            bukuYangHarusKembali = bukuYangKembaliHariIni['COUNT(*)']  # The count of books returned today
        
        # Redirect to home page  
        return render_template('homestaff.html', current_date=current_date, 
                                bukuYangMasihDiPinjam=bukuYangMasihDiPinjam,
                                bukuYangHarusKembali=bukuYangHarusKembali,
                                bukuYangTerlambat=bukuYangTerlambat,
                                hasilPeminjaman=hasilPeminjaman, 
                                hasilPengembalian=hasilPengembalian, 
                                nama_staff=session['nama_staff'], id_staff=session['id_staff'])
    # User is not loggedin redirect to login page
    return redirect(url_for('loginstaff'))

# http://localhost:5000/profilestaff - this will be the profile page, only accessible for logged in users
@app.route('/profilestaff')
def profilestaff():
    # Check if the user is logged in
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM staff WHERE id_staff = %s', (session['id_staff'],))
        akun= cursor.fetchone()
        # Show the profile page with account info        
        return render_template('profilestaff.html', account=akun)
    # User is not logged in redirect to login page
    return redirect(url_for('homestaff'))

# http://localhost:5000/chpwdstaff  the following will be our login page, which will use both GET and POST requests
@app.route('/chpwdstaff', methods=['GET', 'POST'])
def chpwdstaff():  
    # Check if the user is logged in
    if 'loggedin' in session:
        # Output message if something goes wrong...
        msg = ''
        # Change "password" POST requests exist (user submitted form)
        if request.method == 'POST' and 'passwordbr' in request.form:
            # Create variables for easy access
            id_staff=session['id_staff']
            passwordbr = request.form['passwordbr']
            passwordbr1 = request.form['passwordbr1']        
            
            if passwordbr != passwordbr1:
                msg = ('Password tidak sama!, Harap diulang')
                return render_template('chpwdstaff.html', id_staff=session['id_staff'], nama_staff=session['nama_staff'], msg=msg)
            
            # Retrieve the hashed password
            hash = passwordbr + app.secret_key
            hash = hashlib.sha1(hash.encode())
            passwordbr = hash.hexdigest()
        
            # Check if account exists using MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM staff WHERE id_staff = %s', (session['id_staff'],))
            # Fetch one record and return the result
            akun = cursor.fetchone()
            # If akun exists in login table in out database
            if akun:
                # update data password          
                # Update query
                cursor.execute('UPDATE staff SET password = %s WHERE id_staff = %s', (passwordbr, id_staff))
                mysql.connection.commit()            
                # Redirect to home page            
                return render_template('homestaff.html', id_staff=session['id_staff'], nama_staff=session['nama_staff'])
                       
            else:
                # Akun doesnt exist or username/password incorrect
             msg = ('Id Anggota tidak ada!')
        # Show the login form with message (if any)
        return render_template('chpwdstaff.html', id_staff=session['id_staff'], nama_staff=session['nama_staff'], msg=msg)
    
# http://localhost:5000/lupa_password_anggota  the following will be our login page, which will use both GET and POST requests
@app.route('/lupa_password_anggota', methods=['GET', 'POST'])
def lupa_password_anggota():
    msg = ''
    if request.method == 'POST':
        print("Form submitted")
        pencarian = request.form['pencarian']
        print(f"Search query: {pencarian}")
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT * FROM anggota 
            WHERE no_telp_anggota = %s OR id_anggota = %s OR email_anggota = %s
        ''', (pencarian, pencarian, pencarian))
        
        # Use fetchall() to get all matching records
        hasilPencarian = cursor.fetchall()
        
        print('Hasil pencarian:', hasilPencarian)  # Debugging output
        
        if hasilPencarian:
            msg = 'Data anda ditemukan'
            return render_template('lupa_password_anggota.html', hasilPencarian=hasilPencarian, msg=msg)    
        else:
            msg = "Tidak ada data tersebut! Atau silahkan tanya ke Staff tentang ID anda."
            return render_template('lupa_password_anggota.html', msg=msg)

    # Render the registration page with the next available new_id_anggota
    return render_template('lupa_password_anggota.html', msg=msg)


# http://localhost:5000/login/registrasistaff - this will be the registration page, we need to use both GET and POST requests
@app.route('/registrasistaff', methods=['GET', 'POST'])
def registrasistaff():
    msg = ''
    new_id_staff = None  # Initialize variable for new ID

    if request.method == 'GET':
        # Handle the first visit to the registrasi page (GET request)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Fetch the last used id_staff from the database
        cursor.execute('SELECT id_staff FROM staff ORDER BY id_staff DESC LIMIT 1;')
        last_idStaff = cursor.fetchone()

        if last_idStaff:
            # If there are existing entries, generate the next id_staff
            current_id = last_idStaff['id_staff']  # Use the dictionary key for id_staff
            new_id_number = int(current_id[3:]) + 1  # Assuming ID format "ADMxxx"
            new_id_staff = f"ADM{new_id_number:02d}"
        else:
            # If no entries exist, start from "ADM01"
            new_id_staff = "ADM01"
        
        # Store the generated id in session
        session['new_id_staff'] = new_id_staff

        # Return the page with the new ID and any messages
        return render_template('registrasistaff.html', new_id_staff=new_id_staff, msg=msg)
    
    if request.method == 'POST':   
        # Output message if something goes wrong...
        msg = ''
        # Check if "nmstaff", "password" and "email" POST requests exist (user submitted form)
        if 'nmstaff' in request.form and 'tlpstaff' in request.form and 'shift' in request.form and 'email' in request.form and 'password' in request.form :
            # Create variables for easy access
            new_id_staff = session.get('new_id_staff')  # Correct session key
            nmstaff = request.form['nmstaff']
            tlpstaff = request.form['tlpstaff']
            shift = request.form['shift']
            email = request.form['email']
            password = request.form['password']        
            
            # Check if account exists using MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM staff WHERE id_staff = %s', (new_id_staff,))
            akun = cursor.fetchone()
            # If account exists, show error and validation checks
            if akun:
                msg = 'Account already exists!'            
            elif not re.match(r'[a-zA-Z]+', nmstaff):
                msg = 'Invalid nama staff!'    
            elif not re.match(r'^[0-9]+$', tlpstaff):
                msg = 'Invalid nomor telepon!'     
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'        
            elif not nmstaff or not tlpstaff or not shift or not email or not password :
                msg = 'Please fill out the form!'
            else:
                # Hash the password
                hash = password + app.secret_key
                hash = hashlib.sha1(hash.encode())
                password = hash.hexdigest()
                
                # Akun doesn't exist, and the form data is valid, so insert the new account into the accounts table
                cursor.execute('INSERT INTO staff (id_staff, nama_staff, no_telp_staff, email_staff, shift_kerja, password) VALUES (%s, %s, %s, %s, %s, %s)', 
                               (new_id_staff, nmstaff, tlpstaff, email, shift, password))
                mysql.connection.commit()
                msg = 'User baru telah berhasil ditambahkan!'
                
                # After successfully adding, generate the next ID for the next registration
                cursor.execute('SELECT id_staff FROM staff ORDER BY id_staff DESC LIMIT 1;')
                last_idStaff = cursor.fetchone()
                if last_idStaff:
                    current_id = last_idStaff['id_staff']  # Use the dictionary key for id_staff
                    new_id_number = int(current_id[3:]) + 1  # Assuming ID format "ADMxxx"
                    new_id_staff = f"ADM{new_id_number:02d}"

                # Store the new ID in session for the next registration
                session['new_id_staff'] = new_id_staff

        else:
            msg = 'Please fill out the form!'
        
        # Show the staff form with message (if any)
        return render_template('registrasistaff.html', new_id_staff=new_id_staff, msg=msg)
    
# http://localhost:5000/login/firstregistrasistaff - this will be the registration page, we need to use both GET and POST requests
@app.route('/firstregistrasistaff', methods=['GET', 'POST'])
def firstregistrasistaff():
    msg = ''
    new_id_staff = None  # Initialize variable for new ID

    if request.method == 'GET':
        # Handle the first visit to the registrasi page (GET request)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Fetch the last used id_staff from the database
        cursor.execute('SELECT id_staff FROM staff ORDER BY id_staff DESC LIMIT 1;')
        last_idStaff = cursor.fetchone()

        if last_idStaff:
            # If there are existing entries, generate the next id_staff
            current_id = last_idStaff['id_staff']  # Use the dictionary key for id_staff
            new_id_number = int(current_id[3:]) + 1  # Assuming ID format "ADMxxx"
            new_id_staff = f"ADM{new_id_number:02d}"
        else:
            # If no entries exist, start from "ADM01"
            new_id_staff = "ADM01"
        
        # Store the generated id in session
        session['new_id_staff'] = new_id_staff

        # Return the page with the new ID and any messages
        return render_template('firstregistrasistaff.html', new_id_staff=new_id_staff, msg=msg)
    
    if request.method == 'POST':   
        # Output message if something goes wrong...
        msg = ''
        # Check if "nmstaff", "password" and "email" POST requests exist (user submitted form)
        if 'nmstaff' in request.form and 'tlpstaff' in request.form and 'shift' in request.form and 'email' in request.form and 'password' in request.form :
            # Create variables for easy access
            new_id_staff = session.get('new_id_staff')  # Correct session key
            nmstaff = request.form['nmstaff']
            tlpstaff = request.form['tlpstaff']
            shift = request.form['shift']
            email = request.form['email']
            password = request.form['password']        
            
            # Check if account exists using MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM staff WHERE id_staff = %s', (new_id_staff,))
            akun = cursor.fetchone()
            # If account exists, show error and validation checks
            if akun:
                msg = 'Account already exists!'            
            elif not re.match(r'[a-zA-Z]+', nmstaff):
                msg = 'Invalid nama staff!'    
            elif not re.match(r'^[0-9]+$', tlpstaff):
                msg = 'Invalid nomor telepon!'     
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'        
            elif not nmstaff or not tlpstaff or not shift or not email or not password :
                msg = 'Please fill out the form!'
            else:
                # Hash the password
                hash = password + app.secret_key
                hash = hashlib.sha1(hash.encode())
                password = hash.hexdigest()
                
                # Akun doesn't exist, and the form data is valid, so insert the new account into the accounts table
                cursor.execute('INSERT INTO staff (id_staff, nama_staff, no_telp_staff, email_staff, shift_kerja, password) VALUES (%s, %s, %s, %s, %s, %s)', 
                               (new_id_staff, nmstaff, tlpstaff, email, shift, password))
                mysql.connection.commit()
                msg = 'User baru telah berhasil ditambahkan!'
                
                # Store the new ID in session for the next registration
                session['id_staff'] = new_id_staff
                session['nama_staff'] = nmstaff
            
               # Redirect to home page  
                return render_template('homestaff.html', nama_staff=session['nama_staff'], id_staff=session['id_staff'])

        else:
            msg = 'Please fill out the form!'
        
        # Show the staff form with message (if any)
        return render_template('firstregistrasistaff.html', new_id_staff=new_id_staff, msg=msg)


# http://localhost:5000/edtstaff  the following will be our login page, which will use both GET and POST requests
@app.route('/edtstaff', methods=['GET', 'POST'])
def edtstaff():  
    # Check if the user is logged in
    if 'loggedin' in session:
        # Output message if something goes wrong...
        msg = ''
        
        if request.method == 'POST':
            action = request.form.get('action')  # Retrieve the action from the form
            
            if action == "Update":
                # Handle update logic
                # Change the fields POST requests exist (user submitted form)
                if request.method == 'POST' and 'idstaff' in request.form and 'nmstaff' in request.form and 'tlpstaff' in request.form and 'shift' in request.form and 'email' in request.form:
                    # Create variables for easy access
                    id_staff=session['id_staff']
                    nmstaff = request.form['nmstaff']
                    tlpstaff = request.form['tlpstaff']
                    shift = request.form['shift']
                    email = request.form['email']
                        
                    # Check if account exists using MySQL
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute('SELECT * FROM staff WHERE id_staff = %s', (session['id_staff'],))
                    # Fetch one record and return the result
                    akun = cursor.fetchone()
                    # If akun exists in login table in out database
                    if akun:
                        # update data password          
                        # Update query                
                        cursor.execute('UPDATE staff SET nama_staff = %s, no_telp_staff = %s, email_staff = %s, shift_kerja = %s WHERE id_staff = %s', (nmstaff, tlpstaff, email, shift, id_staff))
                        mysql.connection.commit()            
                        # Redirect to home page            
                        return render_template('homestaff.html', id_staff=session['id_staff'], nama_staff=session['nama_staff'])
                            
                    else:
                        # Akun doesnt exist or username/password incorrect
                        msg = ('Id Staff tidak ada!')
            
            elif action == "Hapus":
                # Handle delete logic
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM staff WHERE id_staff = %s', (session['id_staff'],))
                # Fetch one record and return the result
                akun = cursor.fetchone()
                # If akun exists in login table in out database
                if akun:            
                        cursor.execute('DELETE FROM staff WHERE id_staff = %s', (id_staff,))
                        mysql.commit()  # Commit the changes to the database
                        msg = "Record deleted successfully."
                        # Remove session data, this will log the user out
                        session.pop('id_anggota', None)
                        session.pop('nama_anggota', None)
                        session.pop('id_staff', None)   
                        session.pop('nama_staff', None)
                        session.pop('no_telp_staff', None)   
                        session.pop('email_staff', None)
                        session.pop('shift_kerja', None)       
                        return render_template('index.html')
                        
                else:
                    # Akun doesnt exist or username/password incorrect
                    msg = ('Id Staff tidak ada!')              
        
    # Show the login form with message (if any)
    return render_template('edtstaff.html', email_staff=session['email_staff'], 
                           shift_kerja=session['shift_kerja'], 
                           no_telp_staff=session['no_telp_staff'], 
                           id_staff=session['id_staff'], 
                           nama_staff=session['nama_staff'], 
                           msg=msg)

# http://localhost:5000/login/registrasibuku - this will be the registration page, we need to use both GET and POST requests
@app.route('/registrasisbuku', methods=['GET', 'POST'])
def registrasibuku():
    # Output message if something goes wrong...
    msg = ''
    # Check if "idbuku", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'idbuku' in request.form and 'judulbuku' in request.form and 'penulis' in request.form and 'penerbit' in request.form and 'tahunterbit' in request.form and 'jmlhalaman' in request.form and 'jmlbuku' in request.form and 'norak' in request.form :
        # Create variables for easy access
        idbuku = request.form['idbuku']
        judulbuku = request.form['judulbuku']
        penulis = request.form['penulis']
        penerbit = request.form['penerbit']
        tahunterbit = request.form['tahunterbit']
        jmlhalaman = request.form['jmlhalaman'] 
        jmlbuku = request.form['jmlbuku']
        norak = request.form['norak']        
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM buku WHERE id_buku = %s', (idbuku,))
        akun = cursor.fetchone()
        # If akun exists show error and validation checks
        if akun:
            msg = 'Account already exists!'
        elif not re.match(r'[A-Za-z0-9]+', idbuku):
            msg = 'ID Staff must contain only characters and numbers!'
        elif not re.match(r'[a-zA-Z]+', judulbuku):
            msg = 'Invalid judul buku!'    
        elif not re.match(r'[a-zA-Z]+', penulis):
            msg = 'Invalid penulis!'    
        elif not re.match(r'[a-zA-Z]+', penerbit):
            msg = 'Invalid penulis!'        
        elif not re.match(r'[z0-9]+', tahunterbit):
            msg = 'Invalid tahun terbit!'     
        elif not re.match(r'[z0-9]+', jmlhalaman):
            msg = 'Invalid jumlah halamant!'     
        elif not re.match(r'[z0-9]+', jmlbuku):
            msg = 'Invalid jumlah buku!'    
        elif not re.match(r'[A-Za-z0-9]+', norak):
            msg = 'Invalid nomor rak!'    
        elif not idbuku or not judulbuku or not penulis or not penerbit or not tahunterbit  or not jmlhalaman or not jmlbuku or not norak :
            msg = 'Please fill out the form!'
        else:            
            # Akun doesn't exist, and the form data is valid, so insert the new account into the accounts table
            cursor.execute('INSERT INTO buku VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (idbuku, judulbuku, penulis, penerbit, tahunterbit, jmlhalaman, jmlbuku, norak))
            mysql.connection.commit()
            msg = 'Buku telah berhasil ditambahkan!'

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show staff form with message (if any)
    return render_template('registrasibuku.html', msg=msg)

# http://localhost:5000/edtbuku - this will be the registration page, we need to use both GET and POST requests
@app.route('/edtbuku', methods=['GET', 'POST'])
def edtbuku():
    msg = ''
    selected_book = None

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id_buku, judul_buku FROM buku')
    books = cursor.fetchall()

    if request.method == 'POST':
        idbuku = request.form.get('idbuku')
        
        # Fetch the selected book's details
        cursor.execute('SELECT * FROM buku WHERE id_buku = %s', (idbuku,))
        selected_book = cursor.fetchone()
    
        if all(field in request.form for field in ['judulbuku', 'penulis', 'penerbit', 'tahunterbit', 'jmlhalaman', 'jmlbuku', 'norak']):
            # Update book details
            judulbuku = request.form['judulbuku']
            penulis = request.form['penulis']
            penerbit = request.form['penerbit']
            tahunterbit = request.form['tahunterbit']
            jmlhalaman = request.form['jmlhalaman']
            jmlbuku = request.form['jmlbuku']
            norak = request.form['norak']

            cursor.execute('UPDATE buku SET judul_buku=%s, penulis=%s, penerbit=%s, tahun_terbit=%s, jml_halaman=%s, jml_buku=%s, no_rak=%s WHERE id_buku=%s',
                            (judulbuku, penulis, penerbit, tahunterbit, jmlhalaman, jmlbuku, norak, idbuku))
            mysql.connection.commit()
            msg = 'Book details updated successfully!'
    return render_template('edtbuku.html', books=books, selected_book=selected_book, msg=msg)

# http://localhost:5000/delbuku - this will be the registration page, we need to use both GET and POST requests
@app.route('/delbuku', methods=['GET', 'POST'])
def delbuku():
    msg = ''
    selected_book = None

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id_buku, judul_buku FROM buku')
    books = cursor.fetchall()

    if request.method == 'POST':
        idbuku = request.form.get('idbuku')
        
        # Fetch the selected book's details
        cursor.execute('SELECT * FROM buku WHERE id_buku = %s', (idbuku,))
        selected_book = cursor.fetchone()
        
        # Fetch the selected book's details
       
        cursor.execute('DELETE FROM buku WHERE id_buku=%s', (idbuku,))
        mysql.connection.commit()
        cursor.close()
        msg = 'Book deleted successfully!'         
    return render_template('delbuku.html', books=books, selected_book=selected_book, msg=msg)


# http://localhost:5000/browseanggotastaffmenu - this will be the home page, only accessible for logged in users
@app.route('/browseanggotastaffmenu') 
def browseanggotastaffmenu(): 
    # Check if the user is logged in
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM anggota")        
        akunanggota = cursor.fetchall()   
        cursor.close()        
        return render_template('browseanggotastaffmenu.html', akunanggota=akunanggota) 
    # User is not logged in redirect to login page
    return redirect(url_for('homestaff.html'))

# http://localhost:5000/browsestaffstaffmenu - this will be the home page, only accessible for logged in users
@app.route('/browsestaffstaffmenu') 
def browsestaffstaffmenu(): 
    # Check if the user is logged in
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM staff")        
        akunstaff = cursor.fetchall()   
        cursor.close()        
        return render_template('browsestaffstaffmenu.html', akunstaff=akunstaff) 
    # User is not logged in redirect to login page
    return redirect(url_for('homestaff.html'))

# http://localhost:5000/browsebuku - this will be the home page, only accessible for logged in users
@app.route('/browsebuku') 
def browsebuku(): 
    # Check if the user is logged in
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM buku")        
        akunbuku = cursor.fetchall()   
        cursor.close()        
        return render_template('browsebuku.html', akunbuku=akunbuku) 
    # User is not logged in redirect to login page
    return redirect(url_for('home.html'))


# http://localhost:5000/browsebukustaffmenu - this will be the home page, only accessible for logged in users
@app.route('/browsebukustaffmenu') 
def browsebukustaffmenu(): 
    # Check if the user is logged in
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM buku")        
        akunbuku = cursor.fetchall()   
        cursor.close()        
        return render_template('browsebukustaffmenu.html', akunbuku=akunbuku) 
    # User is not logged in redirect to login page
    return redirect(url_for('homestaff.html'))

# http://localhost:5000/peminjaman - this will be the registration page, we need to use both GET and POST requests
@app.route('/peminjaman', methods=['GET', 'POST'])
def peminjaman():
    # Logic for handling book selection and fetching details
    msg = ''
    msg = request.args.get('msg', '')  # Retrieve msg from URL if it exists
    selected_book = None
    idbuku = None  # Initialize id_buku
    id_anggota = session.get('id_anggota')  # Get id_anggota from session
    akunbuku = session.get('akunbuku', [])  # Initialize akunbuku here
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    #cursor.execute('SELECT id_buku, judul_buku FROM buku WHERE jml_buku > 0')
    cursor.execute('SELECT id_buku, judul_buku FROM buku')
    books = cursor.fetchall()

    if request.method == 'POST':
        idbuku = request.form.get('idbuku')
        if 'detail_buku' in request.form:
            # Fetch the selected book's details
            cursor.execute('SELECT * FROM buku WHERE id_buku = %s', (idbuku,))
            selected_book = cursor.fetchone()  
            #print("Selected book details:", selected_book)  # Debugging line          
            
        # Redirect to the new route for "Pilih"
        if 'pilih' in request.form:                        
                #print("Updated akunbuku after 'Pilih':", session['akunbuku'])  # Debugging line
                return redirect(url_for('insert_peminjaman', idbuku=idbuku))
        
        # Redirect to the new route for "details" and selected_book
        if 'details' in request.form:
            #if selected_book:                
                return redirect(url_for('details_peminjaman', idbuku=idbuku))
            
             
    # Close the cursor after all operations
    cursor.close()   
    #print("Final akunbuku before rendering:", akunbuku)  # Debugging line 
    return render_template('peminjaman.html', books=books, selected_book=selected_book, id_anggota=id_anggota, akunbuku=akunbuku, msg=msg)
    
  
@app.route('/insert_peminjaman', methods=['GET', 'POST'])
def insert_peminjaman():
    from datetime import date, timedelta     
    tanggal = date.today()
    str_date = tanggal.strftime('%Y-%m-%d')
    idbuku = request.args.get('idbuku')
    id_anggota = session.get('id_anggota')  
    id_staff=[]
        
    # Check jml_buku in table buku
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT jml_buku FROM buku WHERE id_buku = %s', (idbuku,))
    buku = cursor.fetchone()    
    
    # Check how many books the user has borrowed
    cursor.execute('SELECT COUNT(*) as count FROM peminjaman WHERE id_anggota = %s AND tanggal_pinjam = %s', (id_anggota, str_date))
    borrowed_count = cursor.fetchone()['count']
    session['id_staff']=id_staff
    #print('borrowed_count:', borrowed_count)
    
    # Check if id_anggota and id_buku found in table peminjaman
    cursor.execute('SELECT id_anggota, id_buku FROM peminjaman WHERE id_anggota = %s AND id_buku = %s', (id_anggota, idbuku))
    borrowed_book = cursor.fetchone()
    
    if borrowed_book:
        msg="Buku sedang anda pinjam dan belum kembali!, Detail buku yang dipinjam ada di halaman Home"
        return redirect(url_for('peminjaman', msg=msg))
           
    # Check if buku is None or if jml_buku is 0
    if idbuku and id_anggota and (buku is not None and int(buku['jml_buku']) > 0) and borrowed_count <= 1:               
        cursor = mysql.connection.cursor()        
        # Fetch the last id_pinjam
        cursor.execute('SELECT id_pinjam FROM peminjaman ORDER BY id_pinjam DESC LIMIT 1;')
        last_id = cursor.fetchone()

        # Check if any id was fetched
        if last_id:
            # Extract the ID and increment it
            current_id = last_id[0]  # Access the first element of the tuple
            new_id_number = int(current_id[1:]) + 1  # Increment the numeric part
            new_id_pinjam = f"B{new_id_number:03}"  
        else:
            # check in pengembalian the last id_pinjam
            cursor.execute('SELECT id_pinjam FROM pengembalian ORDER BY id_pinjam DESC LIMIT 1;')
            last_id = cursor.fetchone()
            if last_id:
                current_id = last_id[0]  # Access the first element of the tuple
                new_id_number = int(current_id[1:]) + 1  # Increment the numeric part
                new_id_pinjam = f"B{new_id_number:03}"  
            else:
                # If there are no entries, start from "B001"
                new_id_pinjam = "B001"

        # Now you can use new_id_pinjam for your insert
        cursor.execute('INSERT INTO peminjaman (id_pinjam, tanggal_pinjam, id_buku, id_anggota) VALUES (%s, %s, %s, %s)', 
                       (new_id_pinjam, str_date, idbuku, id_anggota))
        mysql.connection.commit()
        
        # Update stok buku
        now_jml_buku=1        
        cursor.execute('UPDATE buku SET jml_buku = jml_buku - %s WHERE id_buku = %s', (now_jml_buku, idbuku))
        mysql.connection.commit()   
              
        session['tgl_pinjam']=str_date
        msg = 'Peminjaman details inserted successfully!'        
        return redirect(url_for('peminjaman', msg=msg))
    
    else:
        msg='Quota Peminjaman buku adalah 2 buku. / Buku sudah habis dipinjam!'
    return redirect(url_for('peminjaman', msg=msg))

    
@app.route('/details_peminjaman', methods=['GET', 'POST'])
def details_peminjaman():
    # Get the id_anggota from the session
    id_anggota = session.get('id_anggota')

    # Get the current date  
    from datetime import date, timedelta  
    current_date = date.today().strftime('%Y-%m-%d')  # Format: "YYYY-MM-DD"
    tgl_peminjaman=date.today().strftime('%d %B %Y')  # Format: "DD Month YYYY"
    # Calculate next week's date
    next_week_date = (date.today() + timedelta(weeks=1)).strftime('%d %B %Y')  # Format: "DD Month YYYY"

    # Query to fetch details
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
                    SELECT 
                        peminjaman.id_pinjam,
                        peminjaman.tanggal_pinjam,
                        peminjaman.id_buku,
                        peminjaman.id_anggota,
                        buku.judul_buku,
                        buku.penulis,
                        buku.penerbit,
                        buku.tahun_terbit,
                        buku.jml_halaman,
                        buku.jml_buku,
                        buku.no_rak
                    FROM 
                        peminjaman 
                    JOIN 
                        buku ON peminjaman.id_buku = buku.id_buku
                    WHERE 
                        peminjaman.id_anggota = %s
                        AND peminjaman.tanggal_pinjam = %s
                ''', (id_anggota, current_date))

    akunbuku = cursor.fetchall()
        
    return render_template('details_peminjaman.html', 
                           akunbuku=akunbuku, 
                           id_anggota=id_anggota, 
                           nama_anggota=session.get('nama_anggota'), 
                           tgl_peminjaman=tgl_peminjaman,
                           next_week_date=next_week_date)

@app.route('/delete_borrowing', methods=['POST'])
def delete_borrowing():
    data = request.get_json()
    id_pinjam = data.get('id_pinjam')
    id_buku = data.get('id_buku')
    
    # Debug: print received data
    #print(f"Received data: id_pinjam={id_pinjam}, id_buku={id_buku}")

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # Check if id_pinjam and id_buku are provided
        if not id_pinjam or not id_buku:
            return jsonify({"status": "error", "message": "Missing id_pinjam or id_buku"}), 400

        # Check the id_staff existence
        cursor.execute("SELECT id_staff FROM peminjaman WHERE id_pinjam = %s", (id_pinjam,))
        result_idstaff = cursor.fetchone()

        # Debug: print result of id_staff check
        print('result_idstaff:', result_idstaff)

        # Check if id_staff is filled
        if result_idstaff is not None and result_idstaff.get('id_staff'):
            return jsonify({"status": "error", "message": "This borrowing record cannot be deleted because the book has been validated by staff."}), 400
    
         
        # Proceed with the deletion if id_staff is empty
        cursor.execute("SELECT jml_buku FROM buku WHERE id_buku = %s", (id_buku,))
        result = cursor.fetchone()

        if result:
            #and not result_idstaff['id_staff']:
            print('result_idstaff:', result_idstaff)
            current_quantity = int(result['jml_buku'])  # Ensure it's fetched correctly
            new_quantity = current_quantity + 1

            # Update the quantity in the buku table
            cursor.execute("UPDATE buku SET jml_buku = %s WHERE id_buku = %s", (str(new_quantity), id_buku))

            # Delete the borrowing record from peminjaman table
            cursor.execute("DELETE FROM peminjaman WHERE id_pinjam = %s", (id_pinjam,))
            mysql.connection.commit()

            return jsonify({"status": "success", "message": "Borrowing record deleted successfully."}), 200
        else:
            return jsonify({"status": "error", "message": "The Book not found."}), 404

    except Exception as e:
        mysql.connection.rollback()  # Rollback in case of error
        print(f"Error occurred: {str(e)}")  # Log the error for debugging
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        
# http://localhost:5000/pengembalian_buku - this will be the registration page, we need to use both GET and POST requests
@app.route('/pengembalian_buku', methods=['GET', 'POST'])
def pengembalian_buku():    
    # Get the id_anggota from the session
    id_anggota = session.get('id_anggota')

    # Query to fetch details
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
                    SELECT 
                        peminjaman.id_pinjam,
                        peminjaman.tanggal_pinjam,
                        peminjaman.id_buku,
                        peminjaman.id_anggota,
                        buku.judul_buku,
                        buku.penulis,
                        buku.penerbit,
                        buku.tahun_terbit,
                        buku.jml_halaman,
                        buku.jml_buku,
                        buku.no_rak
                    FROM 
                        peminjaman 
                    JOIN 
                        buku ON peminjaman.id_buku = buku.id_buku
                    WHERE 
                        peminjaman.id_anggota = %s   
                        AND peminjaman.id_staff IS NOT NULL 
                        AND peminjaman.id_staff != ''                   
                ''', (id_anggota,))

    akunbuku = cursor.fetchall()
        
    return render_template('pengembalian_buku.html', 
                           akunbuku=akunbuku, 
                           id_anggota=id_anggota, 
                           nama_anggota=session.get('nama_anggota'))
    
@app.route('/pengembalian', methods=['POST'])
def pengembalian():
    data = request.get_json()
    id_pinjam = data.get('id_pinjam')
    tanggal_pinjam=data.get('tanggal_pinjam')
    id_buku = data.get('id_buku')
    #id_anggota = session.get('id_anggota')
    #print('ID Anggota:', id_anggota)
    
    # Get current date
    from datetime import date   
    tanggal = date.today()
    str_date = tanggal.strftime('%Y-%m-%d')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Get the last id_kembali to generate the new one
    cursor.execute('SELECT id_kembali FROM pengembalian ORDER BY id_pinjam DESC LIMIT 1;')
    last_id = cursor.fetchone()

    # Generate new id_kembali
    if last_id and 'id_kembali' in last_id:
        current_id = last_id['id_kembali']
        new_id_number = int(current_id[1:]) + 1  # Increment the numeric part
    else:
        new_id_number = 1  # Start from 1 if there are no entries

    while True:
        new_id_kembali = f"R{new_id_number:03}"  # Format back to string, e.g., R001
        cursor.execute("SELECT COUNT(*) FROM pengembalian WHERE id_kembali = %s", (new_id_kembali,))
        exists = cursor.fetchone()

        if exists and exists['COUNT(*)'] > 0:
            new_id_number += 1  # Increment until a unique ID is found
        else:
            break  # Unique ID found

     # Correctly retrieving id_anggota
    id_anggota = session.get('id_anggota')
    #print('ID Anggota:', id_anggota)
    
    # Debug: print received data
    #print(f"Received data: id_pinjam={id_pinjam}, id_buku={id_buku}")

    if id_anggota is None:
        return jsonify({"status": "error", "message": "User not logged in."}), 401 

    try:
        # Check if id_pinjam and id_buku are provided
        if not id_pinjam or not id_buku:
            return jsonify({"status": "error", "message": "Missing id_pinjam or id_buku"}), 400

        # Check book availability
        cursor.execute("SELECT jml_buku FROM buku WHERE id_buku = %s", (id_buku,))
        result = cursor.fetchone()

        if result:
            # Delete the borrowing record from peminjaman table
            cursor.execute("DELETE FROM peminjaman WHERE id_pinjam = %s", (id_pinjam,))
            mysql.connection.commit()
            
            # Add record to return book in pengembalian table
            cursor.execute('INSERT INTO pengembalian (id_kembali, id_pinjam, id_anggota, tanggal_pinjam, id_buku, tanggal_kembali) VALUES (%s, %s, %s, %s, %s, %s)', 
                       (new_id_kembali, id_pinjam, id_anggota, tanggal_pinjam, id_buku, str_date))
            mysql.connection.commit()

            return jsonify({"status": "success", "message": "Borrowing record deleted successfully."}), 200
        else:
            return jsonify({"status": "error", "message": "The Book not found."}), 404

    except Exception as e:
        mysql.connection.rollback()  # Rollback in case of error
        print(f"Error occurred: {str(e)}")  # Log the error for debugging
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
       
# http://localhost:5000/konfirmasi_peminjaman - this will be the registration page, we need to use both GET and POST requests 
@app.route('/konfirmasi_peminjaman', methods=['GET', 'POST'])
def konfirmasi_peminjaman():
    from datetime import date 
    current_date = date.today().strftime('%Y-%m-%d')  # Format: "YYYY-MM-DD"
    now_date = date.today().strftime('%d %B %Y')  # Format: "DD MMMMM YYYY"
    # Query to fetch details
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
                    SELECT 
                        peminjaman.id_pinjam,
                        peminjaman.tanggal_pinjam,
                        peminjaman.id_buku,
                        peminjaman.id_staff,
                        peminjaman.id_anggota,
                        buku.judul_buku,
                        buku.penulis,
                        buku.penerbit,
                        buku.tahun_terbit,
                        buku.jml_halaman,
                        buku.jml_buku,
                        buku.no_rak,
                        anggota.nama_anggota
                    FROM 
                        peminjaman 
                    JOIN 
                        buku ON peminjaman.id_buku = buku.id_buku
                    JOIN
                        anggota ON peminjaman.id_anggota = anggota.id_anggota
                    WHERE 
                        peminjaman.tanggal_pinjam = %s                        
                    ''', (current_date,))

    akunbuku = cursor.fetchall()    
    #AND (peminjaman.id_staff IS NULL OR peminjaman.id_staff = '')    
    return render_template('konfirmasi_peminjaman.html', akunbuku=akunbuku, now_date=now_date, nama_staff=session.get('nama_staff'), id_staff=session.get('id_staff'))

@app.route('/confirm_borrowing', methods=['POST'])
def confirm_borrowing():
    data = request.get_json()
    id_pinjam = data.get('id_pinjam')
    id_staff = session.get('id_staff')  # Ensure you're getting the correct session variable

    if not id_pinjam or not id_staff:
        return jsonify({"status": "error", "message": "Missing id_pinjam or id_staff"}), 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # Update the database
        cursor.execute("UPDATE peminjaman SET id_staff = %s WHERE id_pinjam = %s", (id_staff, id_pinjam))
        mysql.connection.commit()

        return jsonify({"status": "success", "message": "Borrowing confirmed."}), 200  # Return a success response
    except Exception as e:
        mysql.connection.rollback()  # Rollback if there's an error
        return jsonify({"status": "error", "message": str(e)}), 500  # Return an error response
    finally:
        cursor.close()  # Always close the cursor

# http://localhost:5000/konfirmasi_pengembalian - this will be the registration page, we need to use both GET and POST requests 
@app.route('/konfirmasi_pengembalian', methods=['GET', 'POST'])
def konfirmasi_pengembalian():
    from datetime import date 
    current_date = date.today().strftime('%Y-%m-%d')  # Format: "YYYY-MM-DD"
    now_date = date.today().strftime('%Y-%m-%d')  # Format: "YYYY-MM-DD"
    # Query to fetch details
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
                    SELECT 
                        pengembalian.id_kembali,
                        pengembalian.id_pinjam,
                        pengembalian.tanggal_pinjam,
                        pengembalian.tanggal_kembali,
                        pengembalian.id_buku,
                        pengembalian.id_staff,
                        pengembalian.id_anggota,
                        buku.judul_buku,
                        buku.penulis,
                        buku.penerbit,
                        buku.tahun_terbit,
                        buku.jml_halaman,
                        buku.jml_buku,
                        buku.no_rak,
                        anggota.nama_anggota
                    FROM 
                        pengembalian 
                    JOIN 
                        buku ON pengembalian.id_buku = buku.id_buku
                    JOIN
                        anggota ON pengembalian.id_anggota = anggota.id_anggota   
                    WHERE 
                        pengembalian.tanggal_kembali = %s                                         
                    ''', (current_date,))

    akunpengembalian = cursor.fetchall()    
    #print("Fetched records:", akunpengembalian)
    
    #AND (peminjaman.id_staff IS NULL OR peminjaman.id_staff = '')    
    return render_template('konfirmasi_pengembalian.html', akunpengembalian=akunpengembalian, 
                           nama_staff=session.get('nama_staff'), 
                           now_date=now_date,
                           id_staff=session.get('id_staff'))

@app.route('/returned_book', methods=['POST'])
def returned_book():
    data = request.get_json()   
    #print("Incoming data:", data)  # Debugging output 
    id_pinjam = data.get('id_pinjam')
    id_buku = data.get('id_buku')
    id_staff = session.get('id_staff')  
    tanggal_pinjam_str = data.get('tanggal_pinjam')
    tanggal_kembali_str = data.get('tanggal_kembali')

    if not id_pinjam or not session.get('id_staff'):
        return jsonify({"status": "error", "message": "Missing id_pinjam or id_staff"}), 400

    if not tanggal_pinjam_str or not tanggal_kembali_str:
        return jsonify({"status": "error", "message": "Missing tanggal_pinjam or tanggal_kembali"}), 400

    # Convert strings to datetime
    tanggal_pinjam = datetime.strptime(tanggal_pinjam_str, "%Y-%m-%d")
    tanggal_kembali = datetime.strptime(tanggal_kembali_str, "%Y-%m-%d")

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    dendanya = 1000  # Fine per day
    lamapinjam = (tanggal_kembali - tanggal_pinjam).days  # Calculate the number of days borrowed

    # Check keterlambatan pengembalian buku    
    keterlambatan = max(0, lamapinjam - 7)  # Calculate late days (if any)
    
    if keterlambatan > 0:
        selisih = keterlambatan * dendanya  # Calculate fine for late days
    else:
        selisih = 0

    selisih_str = str(selisih)  # Convert the fine amount to string

    #print('tanggal kembali:', tanggal_kembali)
    #print('tanggal pinjam:', tanggal_pinjam)
    #print('keterlambatan:', keterlambatan)
    #print('Selisih:', selisih_str)
    #print('lamapinjam:', lamapinjam)
    
    try:        
        response = {
            "status": "success",
            "message": "Borrowing record processed successfully.",
            "keterlambatan": lamapinjam ,
            "selisih": selisih
        }   
        # Update the database stock buku         
        cursor.execute('UPDATE buku SET jml_buku = jml_buku + 1 WHERE id_buku = %s', (id_buku,))
        
        # Update the pengembalian table to log the staff and fine       
        cursor.execute("UPDATE pengembalian SET denda = %s, id_staff = %s WHERE id_pinjam= %s", (selisih_str, id_staff, id_pinjam))
        
        # Commit the changes
        mysql.connection.commit()

        return jsonify(response), 200
        #return jsonify({"status": "success", "message": "Borrowing confirmed."}), 200  # Return a success response
    except Exception as e:
        mysql.connection.rollback()  # Rollback if there's an error
        return jsonify({"status": "error", "message": str(e)}), 500  # Return an error response
    finally:
        cursor.close()  # Always close the cursor        

@app.route('/cek_denda', methods=['POST'])
def cek_denda():
    data = request.get_json()
    id_pinjam = data.get('id_pinjam')    
    tanggal_pinjam = datetime.strptime(data.get('tanggal_pinjam'), "%Y-%m-%d")
    tanggal_kembali = datetime.strptime(data.get('tanggal_kembali'), "%Y-%m-%d")

    if not id_pinjam or not session.get('id_staff'):
        return jsonify({"status": "error", "message": "Missing id_pinjam or id_staff"}), 400

    dendanya = 1000  # Fine per day
    lamapinjam = (tanggal_kembali - tanggal_pinjam).days  # Calculate the number of days borrowed

    if lamapinjam > 7:
        selisih = (lamapinjam - 7) * dendanya
    else:
        selisih = 0

    # Check keterlambatan pengembalian buku    
    lamapinjam = (tanggal_kembali - tanggal_pinjam).days  # Total days borrowed
    keterlambatan = max(0, lamapinjam - 7)  # Calculate late days (if any)
   
    if keterlambatan > 0:
        selisih = keterlambatan * dendanya  # Calculate fine for late days
    else:
        selisih = 0

    try:
        response = {
            "status": "success",
            "message": "Borrowing record processed successfully.",
            "keterlambatan": keterlambatan ,
            "selisih": selisih
        }
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# http://localhost:5000/reminder_peminjaman - this will be the registration page, we need to use both GET and POST requests 
@app.route('/reminder_peminjaman', methods=['GET', 'POST'])
def reminder_peminjaman():
    from datetime import date 
    current_date = date.today().strftime('%Y-%m-%d')  # Format: "YYYY-MM-DD"    
    date_str = date.today().strftime('%d %B %Y') 
    
    # Query to fetch details
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
                    SELECT 
                        peminjaman.id_pinjam,
                        peminjaman.tanggal_pinjam,
                        peminjaman.id_buku,
                        peminjaman.id_staff,
                        peminjaman.id_anggota,
                        buku.judul_buku,
                        buku.penulis,
                        buku.penerbit,
                        buku.tahun_terbit,
                        buku.jml_halaman,
                        buku.jml_buku,
                        buku.no_rak,
                        anggota.nama_anggota,
                        staffreminder.remarks                        
                    FROM 
                        peminjaman 
                    JOIN 
                        buku ON peminjaman.id_buku = buku.id_buku
                    JOIN
                        anggota ON peminjaman.id_anggota = anggota.id_anggota  
                    LEFT JOIN
                        staffreminder ON peminjaman.id_pinjam = staffreminder.id_pinjam
                    ''', )

    akunbuku = cursor.fetchall()    
    #print('Akun Buku:', akunbuku)
    
    from datetime import datetime, timedelta
    current_date_str = current_date
    current_date = datetime.strptime(current_date_str, '%Y-%m-%d') 
    
    # Calculate keterlambatan and dendanya
    for buku in akunbuku:
        # Convert tanggal_pinjam to a datetime object
        tanggal_pinjam = datetime.strptime(buku['tanggal_pinjam'], '%Y-%m-%d')
        
        # Set tanggal_kembali
        tanggal_kembali = tanggal_pinjam + timedelta(days=7)
        
        # Check for keterlambatan
        if current_date > tanggal_kembali:  # Now both are datetime objects
            keterlambatan = (current_date - tanggal_kembali).days
            dendanya = keterlambatan * 1000
            buku['keterlambatan'] = keterlambatan
            buku['dendanya'] = dendanya
        else:
            buku['keterlambatan'] = 0
            buku['dendanya'] = 0

        
    #AND (peminjaman.id_staff IS NULL OR peminjaman.id_staff = '')    
    return render_template('reminder_peminjaman.html', 
                       akunbuku=akunbuku, date_str=date_str,
                       nama_staff=session.get('nama_staff'), 
                       id_staff=session.get('id_staff'), 
                       dendanya=session.get('dendanya'), 
                       keterlambatan=session.get('keterlambatan'))

@app.route('/editReminder', methods=['POST'])
def edit_reminder():
    data = request.get_json()
    id_pinjam = data.get('id_pinjam')    

    # Check the id_pinjam existence in staffreminder
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT remarks FROM staffreminder WHERE id_pinjam = %s", (id_pinjam,))
    result_reminder = cursor.fetchone()    

    if result_reminder and 'remarks' in result_reminder:
        return jsonify(result_reminder), 200
    else:        
        return jsonify({"message": "No remarks found for this ID Pinjam."}), 404

@app.route('/getReminder', methods=['POST'])
def get_reminder():
    data = request.get_json()
    id_pinjam = data.get('id_pinjam')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT remarks FROM staffreminder WHERE id_pinjam = %s", (id_pinjam,))
    result = cursor.fetchone()
    
    if result and 'remarks' in result:
        return jsonify(result), 200
    else:
        return jsonify({"remarks": ""}), 404  # Return empty for new entry

@app.route('/updateReminder', methods=['POST'])
def update_reminder():
    data = request.get_json()
    id_pinjam = data.get('id_pinjam')
    remarks = data.get('remarks')    
    id_staff = session.get('id_staff')
    from datetime import date 
    current_date = date.today().strftime('%Y-%m-%d')  # Format: "YYYY-MM-DD"    

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM staffreminder WHERE id_pinjam = %s", (id_pinjam,))
    result = cursor.fetchone()

    if result:  # Update existing record
        cursor.execute("UPDATE staffreminder SET id_staff = %s, tgl_reminder = %s, remarks = %s WHERE id_pinjam = %s", (id_staff, current_date, remarks, id_pinjam))
        message = "Reminder updated successfully!"
    else:  # Insert new record
        cursor.execute("INSERT INTO staffreminder (id_staff, tgl_reminder, id_pinjam, remarks) VALUES (%s, %s, %s, %s)",
                       (id_staff, current_date, id_pinjam, remarks))
        message = "Reminder added successfully!"

    mysql.connection.commit()
    return jsonify({"message": message}), 200    

    
from flask import session, request, jsonify

if __name__ == '__main__':
  app.run()