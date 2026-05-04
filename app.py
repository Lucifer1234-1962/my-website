# ============================================================
# app.py  —  Main Flask application
# Engineering Notes & Quiz Sharing Website
# ============================================================
# HOW TO RUN:
#   1. pip install flask
#   2. python app.py
#   3. Open http://127.0.0.1:5000 in your browser
# ============================================================

import os
import json
from flask import (Flask, render_template, request,
                   redirect, url_for, send_from_directory)
from werkzeug.utils import secure_filename   # keeps filenames safe

# ── App setup ────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "engipdf_secret_123"

# Folder where uploaded PDFs will be saved
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)   # create if it doesn't exist

# Only allow PDF files
ALLOWED_EXTENSIONS = {"pdf"}

# Paths to our JSON "databases"
NOTES_FILE = "data/notes.json"
QUIZ_FILE  = "data/quiz.json"

# ── Helper functions ─────────────────────────────────────────

def allowed_file(filename):
    """Return True only if the file has a .pdf extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_json(filepath):
    """Read a JSON file and return its contents as a Python list.
       Returns an empty list if the file doesn't exist yet."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        return json.load(f)


def save_json(filepath, data):
    """Write a Python list to a JSON file in a readable format."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


# ── Routes ───────────────────────────────────────────────────

# 1. HOME
@app.route("/")
def home():
    notes  = load_json(NOTES_FILE)
    quizzes = load_json(QUIZ_FILE)
    return render_template("index.html",
                           note_count=len(notes),
                           quiz_count=len(quizzes))


# 2. UPLOAD NOTES
@app.route("/upload", methods=["GET", "POST"])
def upload_notes():
    message = ""

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        file  = request.files.get("pdf_file")   # get the uploaded file

        # Validate: title must not be empty
        if not title:
            message = "error_title"

        # Validate: a file must be chosen and it must be a PDF
        elif not file or file.filename == "":
            message = "error_file"

        elif not allowed_file(file.filename):
            message = "error_type"

        else:
            # secure_filename removes dangerous characters from the filename
            filename = secure_filename(file.filename)

            # If a file with the same name already exists, add a number to it
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            counter = 1
            base, ext = os.path.splitext(filename)
            while os.path.exists(save_path):
                filename  = f"{base}_{counter}{ext}"
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                counter  += 1

            file.save(save_path)   # actually save the PDF to disk

            # Save note info to notes.json
            notes = load_json(NOTES_FILE)
            notes.append({
                "id":       len(notes) + 1,
                "title":    title,
                "filename": filename
            })
            save_json(NOTES_FILE, notes)
            message = "success"

    return render_template("upload_notes.html", message=message)


# 3. VIEW NOTES
@app.route("/view-notes")
def view_notes():
    notes = load_json(NOTES_FILE)
    return render_template("view_notes.html", notes=notes)


# 4. SERVE / DOWNLOAD A PDF
# This route lets the browser open or download a PDF from the uploads folder
@app.route("/uploads/<filename>")
def serve_pdf(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# 5. ADD QUIZ QUESTION
@app.route("/add-quiz", methods=["GET", "POST"])
def add_quiz():
    message = ""

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        opt_a    = request.form.get("option_a", "").strip()
        opt_b    = request.form.get("option_b", "").strip()
        opt_c    = request.form.get("option_c", "").strip()
        opt_d    = request.form.get("option_d", "").strip()
        answer   = request.form.get("answer",   "").strip().upper()

        if all([question, opt_a, opt_b, opt_c, opt_d, answer]):
            quizzes = load_json(QUIZ_FILE)
            quizzes.append({
                "id":       len(quizzes) + 1,
                "question": question,
                "options":  {"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d},
                "answer":   answer
            })
            save_json(QUIZ_FILE, quizzes)
            message = "success"
        else:
            message = "error"

    return render_template("add_quiz.html", message=message)


# 6. TAKE QUIZ
@app.route("/take-quiz", methods=["GET", "POST"])
def take_quiz():
    quizzes = load_json(QUIZ_FILE)
    score   = None
    results = []

    if request.method == "POST":
        score = 0
        for q in quizzes:
            user_ans = request.form.get(f"answer_{q['id']}", "").upper()
            correct  = q["answer"]
            is_right = (user_ans == correct)
            if is_right:
                score += 1
            results.append({
                "question":   q["question"],
                "options":    q["options"],
                "user_ans":   user_ans if user_ans else "—",
                "correct":    correct,
                "is_correct": is_right
            })

    return render_template("take_quiz.html",
                           quizzes=quizzes,
                           score=score,
                           total=len(quizzes),
                           results=results)


# 7. AI QUIZ PAGE
@app.route("/ai-quiz")
def ai_quiz():
    return render_template("ai_quiz.html")


# ── Start server ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
