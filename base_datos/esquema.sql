CREATE DATABASE IF NOT EXISTS reconocimiento;
USE reconocimiento;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    contrasena VARCHAR(100) NOT NULL,
    rostro_encoding TEXT NOT NULL
);
