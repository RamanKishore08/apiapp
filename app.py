from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import os

app = Flask(__name__)
CORS(app)

# Function to check if the PDF is a resume based on keywords
def is_resume(text):
    required_keywords = ["education", "experience", "skills", "summary", "projects", "certifications", "awards", 
                         "languages", "contact", "qualification", "internships", "work experience", "certificates", 
                         "courses completed", "achievements", "volunteering", "languages known", "contact me"]
    return any(keyword in text.lower() for keyword in required_keywords)

# Function to analyze grammatical errors (placeholder function)
def analyze_grammar(text):
    errors = len(text.split()) // 100
    if errors > 3:
        return "There are some grammatical errors in your resume.", errors
    return "", errors

# Function to analyze the resume and return score and suggestions
def analyze_resume(text):
    score = 0
    suggestions = []

    # Education or Qualification section
    if any(word in text.lower() for word in ["education", "qualification"]):
        score += 20
    else:
        suggestions.append({"suggestion": "Add an Education or Qualification section", "priority": 1})

    # Experience or Internships or Work Experience section
    if any(word in text.lower() for word in ["experience", "internship", "internships", "work experience"]):
        score += 25
    else:
        suggestions.append({"suggestion": "Add a Work Experience or Internships", "priority": 1})

    # Skills section and specific keyword scoring
    skills_keywords = ["java", "python", "c++", "c", "full stack", "react", "angular", "mern"]
    skills_found = [skill for skill in skills_keywords if skill in text.lower()]
    if skills_found:
        score += len(skills_found) * 5  # Assign 5 points for each skill found, max 35 points
        score = min(score, 35)

    # Projects section
    if "projects" in text.lower():
        score += 12
    else:
        suggestions.append({"suggestion": "Mention relevant projects", "priority": 2})

    # Certifications or Courses Completed section
    if any(word in text.lower() for word in ["certification", "certificates", "courses completed"]):
        score += 8
    else:
        suggestions.append({"suggestion": "Add certifications or completed courses relevant to the field", "priority": 3})

    # Awards or Achievements or Volunteering section
    if any(word in text.lower() for word in ["awards", "achievements", "volunteering"]):
        score += 6
    else:
        suggestions.append({"suggestion": "Include any awards, achievements, or volunteering experience", "priority": 3})

    # Languages section                                   
    if any(word in text.lower() for word in ["languages", "languages known"]):
        score += 6
    else:
        suggestions.append({"suggestion": "Mention languages you are proficient in", "priority": 3})

    # Contact Information section
    if any(word in text.lower() for word in ["contact", "contact me", "phone", "email"]):
        score += 7
    else:
        suggestions.append({"suggestion": "Provide contact information", "priority": 1})

    # Text length suggestion
    if len(text) < 500:
        suggestions.append({"suggestion": "The resume is too short. Add more content.", "priority": 3})
    elif len(text) > 5000:
        suggestions.append({"suggestion": "The resume is too long. Keep it concise.", "priority": 2})

    # Grammar error check
    grammar_suggestion, error_count = analyze_grammar(text)
    if error_count > 0:
        score -= min(5, error_count)  # Reduce score by up to 5 points for grammar errors
        if grammar_suggestion:
            suggestions.append({"suggestion": grammar_suggestion, "priority": 1})

    # Cap the score at 95
    score = min(score, 95)

    return score, suggestions


# Route to check individual resume and return the score
@app.route("/score", methods=["POST"])
def check_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No resume uploaded"}), 400

    resume = request.files["resume"]
    file_path = os.path.join("uploads", resume.filename)

    try:
        os.makedirs("uploads", exist_ok=True)
        resume.save(file_path)

        # Extract text from the resume using pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

        # Check if the file is a valid resume
        if not is_resume(text):
            return jsonify({"error": "Uploaded file is not a valid resume."}), 400

        # Get score and suggestions
        score, suggestions = analyze_resume(text)
        return jsonify({"score": score, "suggestions": [s["suggestion"] for s in suggestions]})

    except Exception as e:
        return jsonify({"error": "Error processing resume."}), 500

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# Route to handle multiple resumes and return the best 5
@app.route("/best5", methods=["POST"])
def best_5_resumes():
    if "resumes" not in request.files:
        return jsonify({"error": "No resumes uploaded"}), 400

    resumes = request.files.getlist("resumes")
    scored_resumes = []

    for resume in resumes:
        file_path = os.path.join("uploads", resume.filename)

        try:
            os.makedirs("uploads", exist_ok=True)
            resume.save(file_path)

            # Extract text from the resume using pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""

            # Check if the file is a valid resume
            if not is_resume(text):
                continue

            # Get score and suggestions
            score, suggestions = analyze_resume(text)
            scored_resumes.append({"filename": resume.filename, "score": score, "suggestions": [s["suggestion"] for s in suggestions]})

        except Exception as e:
            continue

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    best_resumes = sorted(scored_resumes, key=lambda x: x["score"], reverse=True)[:5]
    return jsonify({"best_resumes": best_resumes})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
