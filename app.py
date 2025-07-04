import os
from flask import Flask, request, jsonify, render_template
from pypdf import PdfReader
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Flask app
app = Flask(__name__)

def extract_text_from_pdf(file_stream):
    reader = PdfReader(file_stream)
    text = "\n".join([page.extract_text() or "" for page in reader.pages])
    return text

def extract_keywords(text):
    return set(re.findall(r"\b[a-zA-Z]{3,}\b", text.lower()))



def get_chatgpt_suggestions(resume_text, jd_text, missing_keywords):
    prompt = (
        f"My resume:\n{resume_text[:3000]}\n\n"
        f"Job description:\n{jd_text[:2000]}\n\n"
        f"These keywords are missing: {', '.join(missing_keywords)}.\n"
        "Suggest a few bullet points I can add to improve alignment."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert resume reviewer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

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
    suggestions = get_chatgpt_suggestions(resume_text, jd_text, missing)

    return jsonify({
        'score': score,
        'missing_keywords': missing,
        'suggestions': suggestions
    })

if __name__ == '__main__':
    app.run(debug=True)
