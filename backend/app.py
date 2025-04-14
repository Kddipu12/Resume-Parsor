from flask import Flask, request, jsonify
from flask_cors import CORS
from pdfminer.high_level import extract_text
import re
import json
import os
from datetime import datetime
import sqlite3
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Download required NLTK data
for package in ['punkt', 'stopwords', 'wordnet']:
    try:
        nltk.data.find(f'tokenizers/{package}')
    except LookupError:
        nltk.download(package)

app = Flask(__name__)
CORS(app)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS resumes
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         filename TEXT,
         email TEXT,
         phone TEXT,
         skills TEXT,
         work_experience TEXT,
         raw_text TEXT,
         upload_date TEXT)
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         title TEXT,
         description TEXT,
         created_date TEXT)
    ''')
    conn.commit()
    conn.close()

init_db()

def extract_email(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else None

def extract_phone(text):
    phone_pattern = r'\b(?:\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b'
    phones = re.findall(phone_pattern, text)
    return phones[0] if phones else None

def extract_skills(text):
    # This is a basic list of skills to detect - expand based on requirements
    common_skills = ['python', 'java', 'javascript', 'react', 'node.js', 'sql', 'mongodb',
                     'aws', 'docker', 'kubernetes', 'machine learning', 'data analysis']
    skills = []
    text_lower = text.lower()
    for skill in common_skills:
        if skill in text_lower:
            skills.append(skill)
    return skills

def extract_work_experience(text):
    # Simple extraction based on common keywords
    exp_keywords = ['experience', 'work history', 'employment']
    lines = text.split('\n')
    experience = []
    is_exp_section = False
    
    for line in lines:
        if any(keyword in line.lower() for keyword in exp_keywords):
            is_exp_section = True
            continue
        if is_exp_section and line.strip():
            experience.append(line.strip())
        if is_exp_section and not line.strip():
            is_exp_section = False
    
    return experience[:5]  # Return first 5 entries

def preprocess_text(text):
    # Tokenize
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords and lemmatize
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens if token.isalnum() and token not in stop_words]
    
    return ' '.join(tokens)

from transformers import BertTokenizer, BertModel
import torch

def calculate_similarity(job_text, resume_text):
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')

    def get_embeddings(text):
        inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).squeeze()

    job_embedding = get_embeddings(job_text)
    resume_embedding = get_embeddings(resume_text)

    similarity = cosine_similarity(job_embedding.numpy().reshape(1, -1), resume_embedding.numpy().reshape(1, -1))[0][0]
    
    return round(similarity * 100, 2)

def get_db_connection():
    conn = sqlite3.connect('resumes.db')
    conn.row_factory = sqlite3.Row  # Allows for dictionary-like access to rows
    return conn

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400

    # Save the PDF temporarily
    temp_path = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file.save(temp_path)

    try:
        # Extract text from PDF
        text = extract_text(temp_path)
        
        # Extract information
        parsed_data = {
            'email': extract_email(text),
            'phone': extract_phone(text),
            'skills': extract_skills(text),
            'work_experience': extract_work_experience(text),
            'raw_text': text,
            'filename': file.filename,
            'upload_date': datetime.now().isoformat()
        }

        # Store in SQLite
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO resumes 
            (filename, email, phone, skills, work_experience, raw_text, upload_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            file.filename,
            parsed_data['email'],
            parsed_data['phone'],
            json.dumps(parsed_data['skills']),
            json.dumps(parsed_data['work_experience']),
            parsed_data['raw_text'],
            parsed_data['upload_date']
        ))
        conn.commit()
        conn.close()
        
        # Remove temporary file
        os.remove(temp_path)
        
        return jsonify(parsed_data), 200

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': str(e)}), 500

@app.route('/resumes', methods=['GET'])
def get_resumes():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT filename, email, phone, skills, work_experience, upload_date FROM resumes')
        rows = c.fetchall()
        conn.close()
        
        resumes = []
        for row in rows:
            resume = {
                'filename': row['filename'],
                'email': row['email'],
                'phone': row['phone'],
                'skills': json.loads(row['skills']),
                'work_experience': json.loads(row['work_experience']),
                'upload_date': row['upload_date']
            }
            resumes.append(resume)
        
        return jsonify(resumes)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['GET'])
def search_resumes():
    try:
        skill = request.args.get('skill', '').lower().strip()
        if not skill:
            return jsonify({'error': 'No search term provided'}), 400
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT filename, email, phone, skills, work_experience, upload_date FROM resumes')
        rows = c.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            try:
                skills = json.loads(row['skills'])
                # Convert all skills to lowercase for comparison
                skills_lower = [s.lower() for s in skills]
                
                # Check if the search term is a substring of any skill
                if any(skill in s for s in skills_lower):
                    resume = {
                        'filename': row['filename'],
                        'email': row['email'],
                        'phone': row['phone'],
                        'skills': skills,
                        'work_experience': json.loads(row['work_experience']),
                        'upload_date': row['upload_date']
                    }
                    results.append(resume)
            except json.JSONDecodeError:
                continue  # Skip this resume if skills JSON is invalid
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/jobs', methods=['POST'])
def create_job():
    data = request.get_json()
    if not data or 'title' not in data or 'description' not in data:
        return jsonify({'error': 'Missing title or description'}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO jobs (title, description, created_date)
        VALUES (?, ?, ?)
    ''', (data['title'], data['description'], datetime.now().isoformat()))
    job_id = c.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'id': job_id,
        'title': data['title'],
        'description': data['description']
    }), 201

@app.route('/quick-match', methods=['POST'])
def quick_match_resumes():
    data = request.get_json()
    if not data or 'description' not in data:
        return jsonify({'error': 'Missing job description'}), 400
    
    job_description = data['description']
    
    # Get all resumes
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, filename, email, skills, raw_text FROM resumes')
    resumes = c.fetchall()
    conn.close()
    
    # Calculate match scores
    matches = []
    for resume in resumes:
        resume_id, filename, email, skills, raw_text = resume
        match_score = calculate_similarity(job_description, raw_text)
        
        # Parse skills from JSON string
        skills_list = json.loads(skills)
        
        matches.append({
            'resume_id': resume_id,
            'filename': filename,
            'email': email,
            'skills': skills_list,
            'match_score': match_score
        })
    
    # Sort by match score in descending order
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return jsonify(matches)

@app.route('/jobs/<int:job_id>/match', methods=['GET'])
def match_resumes(job_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get job description
    c.execute('SELECT description FROM jobs WHERE id = ?', (job_id,))
    job_row = c.fetchone()
    if not job_row:
        conn.close()
        return jsonify({'error': 'Job not found'}), 404
    
    job_description = job_row['description']
    
    # Get all resumes
    c.execute('SELECT id, filename, email, skills, raw_text FROM resumes')
    resumes = c.fetchall()
    conn.close()
    
    # Calculate match scores
    matches = []
    for resume in resumes:
        resume_id, filename, email, skills, raw_text = resume
        match_score = calculate_similarity(job_description, raw_text)
        
        # Parse skills from JSON string
        skills_list = json.loads(skills)
        
        matches.append({
            'resume_id': resume_id,
            'filename': filename,
            'email': email,
            'skills': skills_list,
            'match_score': match_score
        })
    
    # Sort by match score in descending order
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return jsonify(matches)

@app.route('/jobs', methods=['GET'])
def get_jobs():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, title, description FROM jobs')
    jobs = c.fetchall()
    conn.close()

    return jsonify([{
        'id': job['id'],
        'title': job['title'],
        'description': job['description']
    } for job in jobs])

if __name__ == '__main__':
    app.run(debug=True, port=5001)
