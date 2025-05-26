-- Drop tables if they exist
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS balita;
DROP TABLE IF EXISTS pengukuran;
DROP TABLE IF EXISTS dataset_lvq;
DROP TABLE IF EXISTS parameter_knn;
DROP TABLE IF EXISTS accuracy_history;

-- Create users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    nama_lengkap TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    email TEXT,
    photo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create balita table
CREATE TABLE balita (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nik TEXT UNIQUE NOT NULL,
    nama TEXT NOT NULL,
    tanggal_lahir DATE NOT NULL,
    jenis_kelamin TEXT NOT NULL,
    nama_ortu TEXT NOT NULL,
    alamat TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create pengukuran table
CREATE TABLE pengukuran (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    balita_id INTEGER NOT NULL,
    tanggal_ukur DATE NOT NULL,
    berat_badan REAL NOT NULL,
    tinggi_badan REAL NOT NULL,
    lingkar_lengan REAL NOT NULL,
    status_gizi TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (balita_id) REFERENCES balita (id)
);

-- Create dataset_lvq table
CREATE TABLE dataset_lvq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature1 REAL NOT NULL, -- berat_badan
    feature2 REAL NOT NULL, -- tinggi_badan
    feature3 REAL NOT NULL, -- lingkar_lengan
    target TEXT NOT NULL,   -- status_gizi
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create parameter_knn table
CREATE TABLE parameter_knn (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nilai_k INTEGER NOT NULL DEFAULT 3,
    bobot_berat REAL NOT NULL DEFAULT 1.0,
    bobot_tinggi REAL NOT NULL DEFAULT 1.0,
    bobot_lila REAL NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create accuracy_history table
CREATE TABLE accuracy_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    accuracy REAL NOT NULL,
    parameter_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parameter_id) REFERENCES parameter_knn (id)
);

-- Create indexes
CREATE INDEX idx_balita_nik ON balita(nik);
CREATE INDEX idx_pengukuran_balita ON pengukuran(balita_id);
CREATE INDEX idx_pengukuran_tanggal ON pengukuran(tanggal_ukur);
CREATE INDEX idx_dataset_target ON dataset_lvq(target);

-- Insert default admin user
INSERT INTO users (username, password, nama_lengkap, role)
VALUES (
    'admin',
    'pbkdf2:sha256:260000$7ESPqxLxc9kzuXK3$cb21c19268c6f4cdc8dfd7669417ca1b8d0ffb20b27641b558adb86c5e3a84cd',
    'Administrator',
    'admin'
);

-- Insert default KNN parameters
INSERT INTO parameter_knn (nilai_k, bobot_berat, bobot_tinggi, bobot_lila)
VALUES (3, 1.0, 1.0, 1.0);