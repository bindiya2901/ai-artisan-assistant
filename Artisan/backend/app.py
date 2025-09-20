from flask import Flask, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import openai
import json

# -----------------------------
# Configuration
# -----------------------------
openai.api_key = "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"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))  # Adjust path to frontend
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__, static_folder=FRONTEND_DIR, template_folder=FRONTEND_DIR)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -----------------------------
# Helper Functions
# -----------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_ai_product_details(title, keywords):
    """
    Generate AI product details: story, marketing caption, SEO keywords, suggested price
    """
    prompt = f"""
    You are an AI assistant for local artisans.
    Product Title: "{title}"
    Keywords: {', '.join(keywords)}

    Generate a JSON output with:
    1. story: 150-200 word compelling product description
    2. captions: 3 catchy marketing captions, max 20 words each
    3. seo_keywords: list of 5-10 SEO keywords
    4. suggested_price: suggested selling price in INR and USD
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7
        )
        content = response.choices[0].message.content.strip()
        try:
            details = json.loads(content)
        except:
            # fallback if AI returns non-JSON
            details = {
                "story": content,
                "captions": [],
                "seo_keywords": keywords,
                "suggested_price": ""
            }
    except Exception as e:
        details = {
            "story": f"Could not generate AI story. Error: {str(e)}",
            "captions": [],
            "seo_keywords": keywords,
            "suggested_price": ""
        }
    return details

# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/create-product', methods=['POST'])
def create_product():
    title = request.form.get('title', '')
    keywords_raw = request.form.get('keywords', '')
    photo = request.files.get('photo')

    if not title or not photo:
        return jsonify({"error": "Title and photo are required"}), 400
    if not allowed_file(photo.filename):
        return jsonify({"error": "Invalid file type"}), 400

    # Save photo
    filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{photo.filename}")
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    photo.save(save_path)
    photo_url = url_for('uploaded_file', filename=filename, _external=False)

    # Prepare keywords
    keywords = [k.strip() for k in keywords_raw.split(',') if k.strip()]

    # Generate AI product details
    details = generate_ai_product_details(title, keywords)
    details["photo_url"] = photo_url
    details["headline"] = f"{title} — Handcrafted with care"

    return jsonify(details), 200

# -----------------------------
# Run App
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
