# CodeChef Auto-Solver (Universal Edition)

An automated script for CodeChef courses that signs in with user credentials, uses **Ask Gemini AI** to solve coding questions, handles quizzes, skips already-solved problems, and advances through modules automatically.

## Quick Start (Any User)

### 1. Install Requirements
```bash
pip install playwright python-dotenv
playwright install chromium
```

### 2. Run Script
```bash
python auto_solve.py
```

## How It Works For Any User:
1. **Login Window**: On first run, Chrome opens to the CodeChef login page. Log in with **Continue with Google** or your username & password.
2. **Auto-Saved Credentials**: Your login cookies are automatically saved to `./storage_state.json` and `./user_data` so you stay logged in.
3. **Ask Gemini AI**: Uses the integrated **Ask Gemini AI** widget to request solution queries.
4. **Auto Resume & Submit**: Automatically clicks **Resume**, injects code, submits, and advances.

## Change Course Target (`.env`)
Create a `.env` file in the project folder to target any course:
```env
COURSE_URL=https://www.codechef.com/learn/course/snist-s3-dbms-2026
```
