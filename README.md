# Resume Parser

A web application that extracts structured data from PDF resumes. Built with Python Flask backend and React frontend.

## Features

- Upload PDF resumes through a modern UI
- Extract key information:
  - Name
  - Email
  - Phone number
  - Skills
  - Work experience
- Store parsed resumes for later access
- Search through resumes by skills
- Clean and intuitive interface

## Prerequisites

- Python 3.8+
- Node.js 14+
- MongoDB

## Setup

1. Clone the repository
2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. Start MongoDB:
   ```bash
   mongod
   ```

5. Access the application at http://localhost:3000

## Usage

1. Click "Select PDF Resume" to choose a PDF file
2. Click "Upload and Parse" to process the resume
3. View extracted information in the summary view
4. Use the search bar to filter resumes by skills
5. View all stored resumes in the list below

## Tech Stack

- Backend: Python Flask
- Frontend: React with Material-UI
- Database: MongoDB
- PDF Processing: pdfminer.six
