import os
from flask import Flask, request, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import pdfplumber
from tqdm import tqdm

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'supersecretkey123'  # Change this for production
ALLOWED_EXTENSIONS = {'txt', 'pdf'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load summarizer at startup
def load_summarizer(model_name="t5-small"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return pipeline("summarization", model=model, tokenizer=tokenizer)

summarizer = load_summarizer()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")
    return text

def read_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Error reading text file: {str(e)}")

def summarize_text(summarizer, text, max_chunk=1000):
    chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
    summaries = []
    for chunk in tqdm(chunks, desc="Summarizing", unit="chunk"):
        try:
            summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
            summaries.append(summary)
        except Exception as e:
            raise Exception(f"Error summarizing chunk: {str(e)}")
    return "\n".join(summaries)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text_input = request.form.get('text_input')
        file = request.files.get('file_input')

        if not text_input and not file:
            flash('Please provide text or upload a file.')
            return redirect(url_for('index'))

        text = None
        try:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                ext = filename.rsplit('.', 1)[1].lower()
                if ext == 'pdf':
                    text = read_pdf(file_path)
                else:
                    text = read_text_file(file_path)
                os.remove(file_path)  # Clean up
            elif text_input:
                text = text_input

            if not text or not text.strip():
                flash('No valid text to summarize.')
                return redirect(url_for('index'))

            summary = summarize_text(summarizer, text)
            return render_template('result.html', summary=summary)

        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
