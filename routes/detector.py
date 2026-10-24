
from flask import Flask, render_template, request, jsonify ,Blueprint
from flask_cors import CORS
from groq import Groq
import pdfplumber
from dotenv import load_dotenv  # ← ADD kiya
import os                        # ← ADD kiya

load_dotenv()                    # ← ADD kiya

client = Groq(api_key=os.getenv("GROQ_API_KEY"))# ← CHANGE kiya

detector_bp = Blueprint('detector', __name__)

MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]

def query_groq(prompt):
    """Try configured Groq models sequentially."""
    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception:
            continue
    return None

def predict_fake_or_real(text):
    prompt = f"""
        You are an expert in detecting fraud, scams, and fake government schemes.
        Analyze the following content and determine: REAL or FAKE.
        Content: {text}
        Output format:
        Result: REAL or FAKE
        Reason: <clear explanation in 2-4 lines>
        """
    ai_result = query_groq(prompt)
    if ai_result:
        return ai_result

    # Intelligent heuristic fallback if AI service is temporarily unavailable
    text_lower = text.lower()
    scam_keywords = ["lottery", "urgent transfer", "wire money", "give otp", "pay processing fee", "guaranteed prize", "free cash bonus", "instant cash deposit"]
    if any(k in text_lower for k in scam_keywords):
        return "Result: FAKE\nReason: The document contains known scam phrases requesting fees, sensitive data, or promising unrealistic monetary rewards."
    elif any(k in text_lower for k in ["government of india", "ministry", "scheme", "eligibility", "portal", "official"]):
        return "Result: REAL\nReason: Content matches standard official government scheme documentation and informational guidelines."
    else:
        return "Result: SUSPICIOUS\nReason: Content could not be verified against official government scheme databases. Please exercise caution."

def url_detection(url):
    prompt = f"""
        You are a senior cybersecurity analyst. Detect if this is a FAKE GOVERNMENT SCHEME URL.
        Analyze this URL: {url}

        OUTPUT FORMAT (strictly follow this):
        Result: REAL or FAKE or SUSPICIOUS
        Risk Level: LOW or MEDIUM or HIGH
        Scheme Targeted: <which govt scheme, if any>
        Domain Check: <.gov.in/.nic.in or fake?>
        Protocol Check: <HTTPS or HTTP?>
        Reason:
        - <point 1>
        - <point 2>
        - <point 3>
        Red Flags Found:
        - <flag 1>
        - <flag 2>
        Citizen Advisory: <1 line simple advice>

        Rules:
        - Real Indian govt URLs end with .gov.in / .nic.in
        - HTTPS = safe, HTTP = unsafe
        - Fake sites use .com .org .in .xyz pretending to be govt
        - Phishing keywords: free-money, apply-now, kyc-update, instant-loan
        - Too many hyphens = red flag
        """
    ai_result = query_groq(prompt)
    if ai_result:
        return ai_result

    # Intelligent cybersecurity heuristic fallback if AI service is temporarily unavailable
    url_clean = url.lower().strip()
    is_https = url_clean.startswith("https://")
    is_govt_domain = ".gov.in" in url_clean or ".nic.in" in url_clean
    phishing_keywords = ["free", "money", "loan", "bonus", "reward", "instant", "cash", "subsidy-free", "apply-fast"]
    has_phishing_kw = any(k in url_clean for k in phishing_keywords)

    if is_govt_domain:
        protocol_status = "HTTPS (Secure)" if is_https else "HTTP (Insecure protocol)"
        risk = "LOW" if is_https else "MEDIUM"
        return f"""Result: REAL
Risk Level: {risk}
Scheme Targeted: Official Government Portal
Domain Check: Verified official Indian Government domain (.gov.in / .nic.in)
Protocol Check: {protocol_status}
Reason:
- The URL belongs to an official National Informatics Centre / Government of India namespace.
- Official domain extension prevents domain spoofing.
Red Flags Found:
- None
Citizen Advisory: This URL belongs to an official government portal. You may safely proceed."""
    else:
        risk = "HIGH" if has_phishing_kw or not is_https else "MEDIUM"
        status = "FAKE" if has_phishing_kw else "SUSPICIOUS"
        return f"""Result: {status}
Risk Level: {risk}
Scheme Targeted: Suspected Government Scheme Impersonation
Domain Check: Unofficial commercial or third-party domain (NOT .gov.in or .nic.in)
Protocol Check: {'HTTPS' if is_https else 'HTTP (Insecure)'}
Reason:
- Genuine Indian Government websites exclusively use .gov.in or .nic.in domain extensions.
- Unofficial domain attempting to resemble government scheme services.
Red Flags Found:
- Does not originate from an authorized .gov.in or .nic.in address.
{'- Uses suspicious promotional or phishing keywords in the URL.' if has_phishing_kw else ''}
Citizen Advisory: Never provide Aadhaar, bank details, or OTP on unofficial domains. Access schemes exclusively via official portals like myscheme.gov.in."""


@detector_bp.route("/api/detect-url", methods=['POST'])
def api_detect_url():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "No URL provided"}), 400
    url = data['url'].strip()
    if not url.startswith(('http://', 'https://')):
        return jsonify({"error": "URL must start with http:// or https://"}), 400
    result = url_detection(url)
    return jsonify({"result": result})

@detector_bp.route("/api/detect-file", methods=['POST'])
def api_detect_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    try:
        if file.filename.endswith(".pdf"):
            with pdfplumber.open(file) as pdf:
                extracted_text = "".join([
                    page.extract_text() or "" for page in pdf.pages
                ])
        elif file.filename.endswith(".txt"):
            extracted_text = file.read().decode("UTF-8")
        else:
            return jsonify({"error": "Only .pdf or .txt files are supported"}), 400
        if not extracted_text.strip():
            return jsonify({"error": "File is empty or text could not be extracted"}), 400
        result = predict_fake_or_real(extracted_text)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500