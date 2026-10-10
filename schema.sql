-- ============================================================
--  MediPredictAI — MySQL Database Schema
--  Run this script ONCE to create the database and all tables.
-- ============================================================

CREATE DATABASE IF NOT EXISTS medical_ai_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE medical_ai_db;

-- ── Users ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(100)  NOT NULL,
  email      VARCHAR(150)  NOT NULL UNIQUE,
  password   VARCHAR(64)   NOT NULL,           -- SHA-256 hex digest
  role       ENUM('patient','doctor','admin') NOT NULL DEFAULT 'patient',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Doctors ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS doctors (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  name           VARCHAR(100) NOT NULL,
  specialization VARCHAR(120) NOT NULL,
  user_id        INT          NOT NULL,         -- links to users.id
  created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── Appointments ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS appointments (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  user_id          INT          NOT NULL,
  doctor_id        INT          NOT NULL,
  appointment_date DATE         NOT NULL,
  symptoms         TEXT,
  status           ENUM('pending','confirmed','completed','cancelled') NOT NULL DEFAULT 'pending',
  created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id)   REFERENCES users(id)   ON DELETE CASCADE,
  FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

-- ── Predictions ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  user_id          INT          NOT NULL,
  symptoms         TEXT         NOT NULL,
  predicted_disease VARCHAR(150) NOT NULL,
  confidence       FLOAT        NOT NULL,
  date             DATETIME     NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── Seed: Admin account ────────────────────────────────────
-- Password: admin123  (SHA-256 = 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa4f4...)
INSERT IGNORE INTO users (name, email, password, role) VALUES
  ('Admin', 'admin@medipredict.ai',
   '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa4f4f99ab8768a2f',
   'admin');

-- Seed: Demo doctor
INSERT IGNORE INTO users (name, email, password, role) VALUES
  ('Dr. Priya Sharma', 'doctor@medipredict.ai',
   '57a3f2c03de3db0c9f8059e5c2e0e39c0b5e18d7a89b8cbf4f0d11e8f5a7b93',
   'doctor');

-- Doctor profile (user_id = 2 assumed; adjust if auto-increment differs)
INSERT IGNORE INTO doctors (name, specialization, user_id)
  SELECT 'Dr. Priya Sharma', 'General Physician', id
  FROM users WHERE email = 'doctor@medipredict.ai';

-- Additional demo doctors
INSERT IGNORE INTO users (name, email, password, role) VALUES
  ('Dr. Arjun Mehta',   'arjun@medipredict.ai',   '57a3f2c03de3db0c9f8059e5c2e0e39c0b5e18d7a89b8cbf4f0d11e8f5a7b93', 'doctor'),
  ('Dr. Kavya Nair',    'kavya@medipredict.ai',    '57a3f2c03de3db0c9f8059e5c2e0e39c0b5e18d7a89b8cbf4f0d11e8f5a7b93', 'doctor'),
  ('Dr. Rohit Verma',   'rohit@medipredict.ai',    '57a3f2c03de3db0c9f8059e5c2e0e39c0b5e18d7a89b8cbf4f0d11e8f5a7b93', 'doctor'),
  ('Dr. Anjali Singh',  'anjali@medipredict.ai',   '57a3f2c03de3db0c9f8059e5c2e0e39c0b5e18d7a89b8cbf4f0d11e8f5a7b93', 'doctor'),
  ('Dr. Suresh Kumar',  'suresh@medipredict.ai',   '57a3f2c03de3db0c9f8059e5c2e0e39c0b5e18d7a89b8cbf4f0d11e8f5a7b93', 'doctor');

INSERT IGNORE INTO doctors (name, specialization, user_id)
  SELECT 'Dr. Arjun Mehta',  'Cardiologist',    id FROM users WHERE email='arjun@medipredict.ai';
INSERT IGNORE INTO doctors (name, specialization, user_id)
  SELECT 'Dr. Kavya Nair',   'Dermatologist',   id FROM users WHERE email='kavya@medipredict.ai';
INSERT IGNORE INTO doctors (name, specialization, user_id)
  SELECT 'Dr. Rohit Verma',  'Neurologist',     id FROM users WHERE email='rohit@medipredict.ai';
INSERT IGNORE INTO doctors (name, specialization, user_id)
  SELECT 'Dr. Anjali Singh', 'Endocrinologist', id FROM users WHERE email='anjali@medipredict.ai';
INSERT IGNORE INTO doctors (name, specialization, user_id)
  SELECT 'Dr. Suresh Kumar', 'Gastroenterologist', id FROM users WHERE email='suresh@medipredict.ai';
