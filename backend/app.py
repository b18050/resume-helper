"""Flask application exposing resume keyword automation with a friendly UI."""
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List

from flask import Flask, jsonify, render_template, request, send_file

from services.ai_keyword_extractor import extract_keywords_via_openai
from services.keyword_extractor import extract_keywords, fetch_job_description
from services.resume_processor import (
    build_white_block,
    find_missing_keywords,
    inject_white_keywords,
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RESUME_FILE = BASE_DIR.parent / "main.tex"
app = Flask(
    __name__,
    static_folder=str(BASE_DIR.parent / "frontend" / "static"),
    template_folder=str(BASE_DIR.parent / "frontend" / "templates"),
)

app.logger.setLevel(logging.INFO)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # limit uploads to 8 MB


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.post("/api/process")
def process_resume():
    warnings: List[str] = []
    
    # Get company name for directory organization
    company_name = request.form.get("company_name", "").strip()
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400
    
    # Sanitize company name for filesystem (remove special characters)
    import re
    safe_company_name = re.sub(r'[^\w\s-]', '', company_name)
    safe_company_name = re.sub(r'[-\s]+', '_', safe_company_name).strip('_')
    
    # Create company directory inside resumes/
    resumes_dir = BASE_DIR.parent / "resumes"
    resumes_dir.mkdir(exist_ok=True)
    
    company_dir = resumes_dir / safe_company_name
    company_dir.mkdir(exist_ok=True)
    
    resume_source = request.form.get("resume_source", "upload")

    resume_content = ""
    if resume_source == "default":
        if not DEFAULT_RESUME_FILE.exists():
            return (
                jsonify(
                    {
                        "error": "Default resume (main.tex) was not found in the project directory. Upload a file instead.",
                    }
                ),
                400,
            )
        try:
            resume_content = DEFAULT_RESUME_FILE.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            resume_content = DEFAULT_RESUME_FILE.read_text(encoding="latin-1")
            warnings.append(
                "Default main.tex was decoded using latin-1 encoding. Consider converting it to UTF-8 for best results."
            )
        except OSError as exc:
            app.logger.error("Unable to read default resume", exc_info=exc)
            return jsonify({"error": "Unable to read default resume file."}), 500
    else:
        resume_file = request.files.get("resume")
        if resume_file is None:
            return jsonify({"error": "Please upload your LaTeX resume (.tex file)."}), 400

        resume_bytes = resume_file.read()
        if not resume_bytes:
            return jsonify({"error": "Uploaded resume is empty."}), 400

        try:
            resume_content = resume_bytes.decode("utf-8")
        except UnicodeDecodeError:
            resume_content = resume_bytes.decode("latin-1")
            warnings.append(
                "Resume was decoded using latin-1 encoding. Consider saving as UTF-8 for best results."
            )

    job_url = request.form.get("job_url", "").strip()
    manual_description = request.form.get("job_description", "").strip()
    scraped_from_url = False

    job_text = ""
    if job_url:
        try:
            job_text = fetch_job_description(job_url)
            scraped_from_url = True
        except RuntimeError as exc:
            warnings.append(str(exc))
            app.logger.warning("Failed to scrape job description", exc_info=exc)

    if not job_text:
        job_text = manual_description

    if not job_text:
        return jsonify({"error": "Provide a job description URL or paste the description text."}), 400

    try:
        target_keywords = int(request.form.get("keyword_target", 20))
    except ValueError:
        target_keywords = 20
    target_keywords = max(1, min(target_keywords, 60))

    use_ai = request.form.get("use_ai_keywords", "false").lower() in {"1", "true", "yes", "on"}

    keyword_candidates = extract_keywords(job_text, max_keywords=target_keywords * 3)
    heuristic_count = len(keyword_candidates)

    ai_keywords: List[str] = []
    if use_ai:
        ai_keywords = extract_keywords_via_openai(
            job_text,
            resume_text=resume_content,
            max_keywords=target_keywords * 2,
        )
        if not ai_keywords:
            warnings.append(
                "AI keyword extraction was requested but produced no results. Confirm OPENAI_API_KEY is configured."
            )

    seen = {kw.lower(): None for kw in keyword_candidates}
    for ai_kw in ai_keywords:
        lowered = ai_kw.lower()
        if lowered not in seen:
            keyword_candidates.append(ai_kw)
            seen[lowered] = None

    app.logger.info(
        "Extracted keywords (heuristic=%d, ai=%d, combined=%d): %s",
        heuristic_count,
        len(ai_keywords),
        len(keyword_candidates),
        ", ".join(keyword_candidates),
    )
    missing_keywords = find_missing_keywords(resume_content, keyword_candidates)
    missing_keywords = missing_keywords[:target_keywords]

    updated_resume, modified, injection_warnings = inject_white_keywords(
        resume_content, missing_keywords
    )
    warnings.extend(injection_warnings)

    white_block = build_white_block(missing_keywords) if missing_keywords else ""
    
    # Save LaTeX file to company directory
    tex_output_path = company_dir / "Chandan_Prakash_Software.tex"
    try:
        tex_output_path.write_text(updated_resume, encoding="utf-8")
        app.logger.info(f"Saved LaTeX to: {tex_output_path}")
    except Exception as exc:
        app.logger.error(f"Failed to save LaTeX file: {exc}")
        warnings.append(f"Could not save .tex file to {safe_company_name}/ directory")

    response_payload = {
        "scraped_from_url": scraped_from_url,
        "keyword_candidates": keyword_candidates,
        "ai_keywords": ai_keywords,
        "ai_enabled": use_ai,
        "missing_keywords": missing_keywords,
        "white_block": white_block,
        "updated_resume": updated_resume,
        "modified": modified,
        "warnings": warnings,
        "company_name": company_name,
        "safe_company_name": safe_company_name,
        "output_dir": f"resumes/{safe_company_name}",
    }
    return jsonify(response_payload)


@app.post("/api/compile-pdf")
def compile_pdf():
    """Compile LaTeX resume to PDF and return the PDF file."""
    try:
        latex_content = request.json.get("latex_content", "")
        company_name = request.json.get("company_name", "").strip()
        
        if not latex_content:
            return jsonify({"error": "No LaTeX content provided"}), 400
        
        # Prepare company directory if name provided
        company_dir = None
        if company_name:
            import re
            safe_company_name = re.sub(r'[^\w\s-]', '', company_name)
            safe_company_name = re.sub(r'[-\s]+', '_', safe_company_name).strip('_')
            
            resumes_dir = BASE_DIR.parent / "resumes"
            resumes_dir.mkdir(exist_ok=True)
            
            company_dir = resumes_dir / safe_company_name
            company_dir.mkdir(exist_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tex_file = tmp_path / "resume.tex"
            pdf_file = tmp_path / "resume.pdf"
            
            # Write LaTeX content to temp file
            tex_file.write_text(latex_content, encoding="utf-8")
            
            # Find pdflatex - check TinyTeX, system PATH, and common locations
            pdflatex_paths = [
                Path.home() / "Library/TinyTeX/bin/universal-darwin/pdflatex",
                "pdflatex",  # Try system PATH
                "/Library/TeX/texbin/pdflatex",  # MacTeX
            ]
            
            pdflatex_cmd = None
            for path in pdflatex_paths:
                path_str = str(path)
                try:
                    result = subprocess.run(
                        [path_str, "--version"],
                        capture_output=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        pdflatex_cmd = path_str
                        break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            if not pdflatex_cmd:
                return jsonify({
                    "error": "pdflatex not found. Please ensure TinyTeX or LaTeX is installed."
                }), 500
            
            # Compile with pdflatex (run twice for proper formatting)
            for _ in range(2):
                result = subprocess.run(
                    [pdflatex_cmd, "-interaction=nonstopmode", "-output-directory", str(tmp_path), str(tex_file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            
            # Check if PDF was created
            if not pdf_file.exists():
                error_log = result.stderr if result.stderr else result.stdout
                app.logger.error("PDF compilation failed: %s", error_log)
                return jsonify({
                    "error": "PDF compilation failed. Check your LaTeX syntax or ensure all required packages are installed."
                }), 500
            
            # Save PDF to company directory if specified
            if company_dir:
                pdf_output_path = company_dir / "Chandan_Prakash_Software.pdf"
                try:
                    import shutil
                    shutil.copy(pdf_file, pdf_output_path)
                    app.logger.info(f"Saved PDF to: {pdf_output_path}")
                except Exception as exc:
                    app.logger.error(f"Failed to save PDF to company directory: {exc}")
            
            # Return the PDF with the specified filename
            return send_file(
                pdf_file,
                mimetype="application/pdf",
                as_attachment=True,
                download_name="Chandan_Prakash_Software.pdf"
            )
            
    except subprocess.TimeoutExpired:
        return jsonify({"error": "PDF compilation timed out"}), 500
    except Exception as exc:
        app.logger.error("PDF compilation error", exc_info=exc)
        return jsonify({"error": f"PDF compilation error: {str(exc)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
