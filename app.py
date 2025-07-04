import os
from flask import Flask, request, jsonify, render_template
from pypdf import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv
import re

load_dotenv()
GEMINI_API_KEY=os.getenv("Genkey")

app=Flask(__name__)
genai.configure(api_key=GEMINI_API_KEY)

def extract_text_from_pdf(file_stream):
    reader = PdfReader(file_stream)
    text = "\n".join([page.extract_text() or "" for page in reader.pages])
    return text

def extract_keywords(text):
    return set(re.findall(r"\b[a-zA-Z]{3,}\b", text.lower()))

def get_gemini_suggestions(resume_text, jd_text, missing_keywords):
    prompt = (
        f"My resume is:\n{resume_text[:3000]}\n\n"
        f"The job description is:\n{jd_text[:2000]}\n\n"
        f"These keywords are missing from my resume: {', '.join(missing_keywords)}.\n"
        "Suggest bullet points I could add to improve alignment."
    )
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text.strip()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_ats():
    resume_file = request.files.get('resume')
    jd_text = request.form.get('jobdesc')

    if not resume_file or not jd_text:
        return jsonify({'error': 'Missing resume or job description'}), 400

    resume_text = extract_text_from_pdf(resume_file.stream)
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd_text)
    missing = sorted(list(jd_keywords - resume_keywords))
    score = int((len(jd_keywords & resume_keywords) / len(jd_keywords)) * 100) if jd_keywords else 0
    suggestions = get_gemini_suggestions(resume_text, jd_text, missing)

    return jsonify({
        'score': score,
        'missing_keywords': missing,
        'suggestions': suggestions
    })

if __name__ == '__main__':
    app.run(debug=True)
