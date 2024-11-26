import mysql.connector
from mysql.connector import Error
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

# Koneksi ke database MySQL
def connect():
    try:
        koneksi = mysql.connector.connect(
            host='localhost',
            port=3066,  # Port XAMPP Anda
            database='library_db',
            user='root',
            password=''
        )
        if koneksi.is_connected():
            print("Terhubung ke MySQL")
        return conn
    except Error as e:
        print(f"Error: {e}")
        return None

# Kelas Buku untuk menyimpan data buku
class Buku:
    def __init__(self, id_buku, judul, penulis):
        self.id_buku = id_buku
        self.judul = judul
        self.penulis = penulis

    def get_id_buku(self):
        return self.id_buku

    def get_judul(self):
        return self.judul

    def get_penulis(self):
        return self.penulis

# Membuat tabel buku dan peminjaman
def create_tables():
    conn = connect()
    if conn:
        cursor = conn.cursor()
        # Tabel Buku
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS buku (
            id_buku INT PRIMARY KEY,
            judul VARCHAR(255),
            penulis VARCHAR(255)
        );
        """)
        # Tabel Peminjaman
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS peminjaman (
            id_peminjaman INT PRIMARY KEY AUTO_INCREMENT,
            nama_peminjam VARCHAR(255),
            id_buku INT,
            tanggal_pinjam DATE,
            tanggal_kembali DATE,
            FOREIGN KEY (id_buku) REFERENCES buku(id_buku)
        );
        """)
        conn.commit()
        cursor.close()
        conn.close()

# Fungsi untuk menambahkan buku
def tambah_buku(buku):
    conn = connect()
    sql = "INSERT INTO buku (id_buku, judul, penulis) VALUES (%s, %s, %s)"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (buku.get_id_buku(), buku.get_judul(), buku.get_penulis()))
            conn.commit()
            messagebox.showinfo("Info", "Buku berhasil ditambahkan!")
    except Error as e:
        messagebox.showerror("Error", f"Error: {e}")
    finally:
        if conn.is_connected():
            conn.close()

# Fungsi untuk meminjam buku
def pinjam_buku(nama_peminjam, id_buku, tanggal_pinjam, tanggal_kembali):
    conn = connect()
    sql = "INSERT INTO peminjaman (nama_peminjam, id_buku, tanggal_pinjam, tanggal_kembali) VALUES (%s, %s, %s, %s)"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (nama_peminjam, id_buku, tanggal_pinjam, tanggal_kembali))
            conn.commit()
            messagebox.showinfo("Info", "Buku berhasil dipinjam!")
    except Error as e:
        messagebox.showerror("Error", f"Error: {e}")
    finally:
        if conn.is_connected():
            conn.close()

# Fungsi untuk melihat notifikasi pengembalian
def notifikasi_pengembalian():
    conn = connect()
    today = datetime.now().date()
    sql = "SELECT id_peminjaman, id_buku, tanggal_kembali FROM peminjaman WHERE tanggal_kembali < %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (today,))
            results = cursor.fetchall()
            if results:
                notifikasi = "\n".join(f"Buku ID {row[1]} harus dikembalikan (ID Peminjaman: {row[0]})" for row in results)
                messagebox.showwarning("Notifikasi Pengembalian", notifikasi)
            else:
                messagebox.showinfo("Notifikasi Pengembalian", "Tidak ada buku yang harus dikembalikan.")
    except Error as e:
        messagebox.showerror("Error", f"Error: {e}")
    finally:
        if conn.is_connected():
            conn.close()

# Fungsi untuk mendapatkan daftar buku
def get_daftar_buku():
    conn = connect()
    sql = "SELECT * FROM buku"
    daftar_buku = []
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            results = cursor.fetchall()
            for row in results:
                daftar_buku.append((row[0], row[1], row[2]))  # ID, Judul, Penulis
    except Error as e:
        messagebox.showerror("Error", f"Error: {e}")
    finally:
        if conn.is_connected():
            conn.close()
    return daftar_buku

# Fungsi untuk mendapatkan daftar peminjaman berdasarkan nama peminjam
def get_daftar_peminjaman(nama_peminjam):
    conn = connect()
    sql = "SELECT id_buku, tanggal_pinjam, tanggal_kembali FROM peminjaman WHERE nama_peminjam = %s"
    daftar_peminjaman = []
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (nama_peminjam,))
            results = cursor.fetchall()
            for row in results:
                daftar_peminjaman.append((row[0], row[1], row[2]))  # ID Buku, Tanggal Pinjam, Tanggal Kembali
    except Error as e:
        messagebox.showerror("Error", f"Error: {e}")
    finally:
        if conn.is_connected():
            conn.close()
    return daftar_peminjaman

# GUI
class LibraryApp:
    def __init__(self, master):
        self.master = master
        master.title("Sistem Manajemen Perpustakaan")

        self.label = tk.Label(master, text="Sistem Manajemen Perpustakaan", font=("Arial", 16))
        self.label.pack()

        self.frame = tk.Frame(master)
        self.frame.pack(pady=20)

        self.peminjam_label = tk.Label(self.frame, text="Nama Peminjam:")
        self.peminjam_label.grid(row=0, column=0)
        self.peminjam_entry = tk.Entry(self.frame)
        self.peminjam_entry.grid(row=0, column=1)

        self.buku_id_label = tk.Label(self.frame, text="ID Buku:")
        self.buku_id_label.grid(row=1, column=0)
        self.buku_id_entry = tk.Entry(self.frame)
        self.buku_id_entry.grid(row=1, column=1)

        self.judul_label = tk.Label(self.frame, text="Judul Buku:")
        self.judul_label.grid(row=2, column=0)
        self.judul_entry = tk.Entry(self.frame)
        self.judul_entry.grid(row=2, column=1)

        self.penulis_label = tk.Label(self.frame, text="Penulis Buku:")
        self.penulis_label.grid(row=3, column=0)
        self.penulis_entry = tk.Entry(self.frame)
        self.penulis_entry.grid(row=3, column=1)

        self.tanggal_pinjam_label = tk.Label(self.frame, text="Tanggal Pinjam (YYYY-MM-DD):")
        self.tanggal_pinjam_label.grid(row=4, column=0)
        self.tanggal_pinjam_entry = tk.Entry(self.frame)
        self.tanggal_pinjam_entry.grid(row=4, column=1)

        self.tanggal_kembali_label = tk.Label(self.frame, text="Tanggal Kembali (YYYY-MM-DD):")
        self.tanggal_kembali_label.grid(row=5, column=0)
        self.tanggal_kembali_entry = tk.Entry(self.frame)
        self.tanggal_kembali_entry.grid(row=5, column=1)

        self.tambah_button = tk.Button(master, text="Tambah Buku", command=self.tambah_buku)
        self.tambah_button.pack(pady=5)

        self.pinjam_button = tk.Button(master, text="Pinjam Buku", command=self.pinjam_buku)
        self.pinjam_button.pack(pady=5)

        self.notifikasi_button = tk.Button(master, text="Notifikasi Pengembalian", command=notifikasi_pengembalian)
        self.notifikasi_button.pack(pady=5)

        self.daftar_buku_button = tk.Button(master, text="Lihat Daftar Buku", command=self.lihat_daftar_buku)
        self.daftar_buku_button.pack(pady=5)

        self.daftar_peminjaman_button = tk.Button(master, text="Lihat Daftar Peminjaman", command=self.lihat_daftar_peminjaman)
        self.daftar_peminjaman_button.pack(pady=5)

    def tambah_buku(self):
        try:
            id_buku = int(self.buku_id_entry.get())
            judul = self.judul_entry.get()
            penulis = self.penulis_entry.get()
            buku_baru = Buku(id_buku, judul, penulis)
            tambah_buku(buku_baru)
            self.buku_id_entry.delete(0, tk.END)
            self.judul_entry.delete(0, tk.END)
            self.penulis_entry.delete(0, tk.END)
            self.tanggal_pinjam_entry.delete(0, tk.END)
            self.tanggal_kembali_entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "ID Buku harus berupa angka!")

    def pinjam_buku(self):
        nama_peminjam = self.peminjam_entry.get()
        id_buku = self.buku_id_entry.get()
        tanggal_pinjam = self.tanggal_pinjam_entry.get()
        tanggal_kembali = self.tanggal_kembali_entry.get()

        pinjam_buku(nama_peminjam, id_buku, tanggal_pinjam, tanggal_kembali)

    def lihat_daftar_buku(self):
        daftar_buku = get_daftar_buku()
        if not daftar_buku:
            messagebox.showinfo("Info", "Tidak ada buku dalam database.")
            return
        
        new_window = tk.Toplevel(self.master)
        new_window.title("Daftar Buku")

        tree = ttk.Treeview(new_window, columns=("ID", "Judul", "Penulis"), show="headings")
        tree.heading("ID", text="ID Buku")
        tree.heading("Judul", text="Judul Buku")
        tree.heading("Penulis", text="Penulis Buku")

        for buku in daftar_buku:
            tree.insert("", tk.END, values=buku)

        tree.pack()

    def lihat_daftar_peminjaman(self):
        nama_peminjam = self.peminjam_entry.get()
        daftar_peminjaman = get_daftar_peminjaman(nama_peminjam)

        if not daftar_peminjaman:
            messagebox.showinfo("Info", "Tidak ada peminjaman untuk pengguna ini.")
            return
        
        new_window = tk.Toplevel(self.master)
        new_window.title("Daftar Peminjaman")

        tree = ttk.Treeview(new_window, columns=("ID Buku", "Tanggal Pinjam", "Tanggal Kembali"), show="headings")
        tree.heading("ID Buku", text="ID Buku")
        tree.heading("Tanggal Pinjam", text="Tanggal Pinjam")
        tree.heading("Tanggal Kembali", text="Tanggal Kembali")

        for peminjaman in daftar_peminjaman:
            tree.insert("", tk.END, values=peminjaman)

        tree.pack()

if __name__ == "__main__":
    create_tables()
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()