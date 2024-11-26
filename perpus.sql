-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 06, 2024 at 02:48 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.1.25

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `perpus`
--

-- --------------------------------------------------------

--
-- Table structure for table `anggota`
--

CREATE TABLE `anggota` (
  `id_anggota` varchar(8) NOT NULL,
  `nama_anggota` varchar(30) NOT NULL,
  `no_telp_anggota` varchar(20) NOT NULL,
  `email_anggota` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `buku`
--

CREATE TABLE `buku` (
  `id_buku` varchar(8) NOT NULL,
  `judul_buku` varchar(255) NOT NULL,
  `penulis` varchar(255) NOT NULL,
  `penerbit` varchar(255) NOT NULL,
  `tahun_terbit` varchar(4) NOT NULL,
  `jml_halaman` varchar(4) NOT NULL,
  `jml_buku` varchar(4) NOT NULL,
  `no_rak` varchar(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `peminjaman`
--

CREATE TABLE `peminjaman` (
  `id_pinjam` varchar(20) NOT NULL,
  `tanggal_pinjam` varchar(10) NOT NULL,
  `id_buku` varchar(8) NOT NULL,
  `id_anggota` varchar(8) NOT NULL,
  `id_staff` varchar(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `pengembalian`
--

CREATE TABLE `pengembalian` (
  `id_kembali` varchar(20) NOT NULL,
  `id_pinjam` varchar(20) NOT NULL,
  `id_anggota` varchar(8) NOT NULL,
  `id_buku` varchar(8) NOT NULL,
  `tanggal_pinjam` varchar(10) NOT NULL,
  `tanggal_kembali` varchar(10) NOT NULL,
  `denda` varchar(8) NOT NULL,
  `id_staff` varchar(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `staff`
--

CREATE TABLE `staff` (
  `id_staff` varchar(5) NOT NULL,
  `nama_staff` varchar(25) NOT NULL,
  `no_telp_staff` varchar(20) NOT NULL,
  `email_staff` varchar(255) NOT NULL,
  `shift_kerja` varchar(8) NOT NULL,
  `password` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `staffreminder`
--

CREATE TABLE `staffreminder` (
  `id_staff` varchar(5) NOT NULL,
  `tgl_reminder` varchar(10) NOT NULL,
  `id_pinjam` varchar(8) NOT NULL,
  `remarks` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `anggota`
--
ALTER TABLE `anggota`
  ADD PRIMARY KEY (`id_anggota`),
  ADD UNIQUE KEY `email_anggota` (`id_anggota`),
  ADD UNIQUE KEY `no_telp_anggota` (`id_anggota`);

--
-- Indexes for table `buku`
--
ALTER TABLE `buku`
  ADD PRIMARY KEY (`id_buku`);

--
-- Indexes for table `peminjaman`
--
ALTER TABLE `peminjaman`
  ADD PRIMARY KEY (`id_pinjam`),
  ADD KEY `idxstaff` (`id_staff`),
  ADD KEY `idxanggota` (`id_anggota`),
  ADD KEY `idxbuku` (`id_buku`),
  ADD KEY `idxtglpinjam` (`tanggal_pinjam`);

--
-- Indexes for table `pengembalian`
--
ALTER TABLE `pengembalian`
  ADD PRIMARY KEY (`id_kembali`),
  ADD KEY `id_pinjam` (`id_pinjam`),
  ADD KEY `id_staff` (`id_staff`);

--
-- Indexes for table `staff`
--
ALTER TABLE `staff`
  ADD PRIMARY KEY (`id_staff`);

--
-- Indexes for table `staffreminder`
--
ALTER TABLE `staffreminder`
  ADD UNIQUE KEY `id_staff` (`id_staff`),
  ADD UNIQUE KEY `id_staff_2` (`id_staff`),
  ADD KEY `id_anggota` (`id_pinjam`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
