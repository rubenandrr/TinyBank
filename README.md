# Tiny Bank

Welcome to **Tiny Bank**, a clean, modular, and thread-safe multi-currency banking simulation. This project is built step-by-step to demonstrate modern software architecture practices, secure transaction logic, and responsive UI design.

---

## Project Overview

Tiny Bank simulates a real-world banking API with support for multiple currencies (CHF, EUR, USD), daily transaction limits, automated taxation, system auditing, and account statement exports.

The project is split into:
- **Backend**: A modular FastAPI application built with Python 3.11, Pydantic V2, and Pytest.
- **Frontend**: A sleek, modern dashboard built with React 18, Vite, TypeScript, and Vanilla CSS utilizing a dark glassmorphism theme.

---

## Development Roadmap (Step-by-Step)

Here is the step-by-step implementation plan for the project:

### 1. Project Setup
- Initialize `.gitignore` and `requirements.txt`.
- Set up a Python virtual environment and install dependencies.

### 2. Core Data Models & Database
- Design Pydantic models for Users, Accounts, and Transactions.
- Create an in-memory database store with a global concurrency lock (`threading.Lock`).

### 3. Business Logic (Services)
- Implement helpers for currency conversion and exchange rates.
- Code services for user creation/deactivation and account management.
- Implement withdrawal and transfer operations with daily limit validation.

### 4. API Endpoints (FastAPI Routers)
- Set up modular routers for `/users`, `/accounts`, `/transfers`, and `/audit`.
- Configure global exception handlers for transaction failures.

### 5. Automation & Testing
- Write Pytest fixtures for database isolation.
- Create unit tests for user management, transaction limits, and multi-currency transfers.

### 6. Containerization & CI/CD
- Write the `Dockerfile` and `docker-compose.yml`.
- Configure GitHub Actions workflow for automated tests on every push.

### 7. Interactive Frontend
- Set up the React + Vite + TypeScript template.
- Implement the glassmorphism CSS theme and navigation system.
- Build components for the user dashboard, money transfers, client administration, and compliance audit logs.
