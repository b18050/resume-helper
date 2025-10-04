#!/usr/bin/env python3
"""
End-to-end test: Process a job description, generate PDF with keywords, 
and verify the keywords are present in the final PDF.
"""
import json
import subprocess
import tempfile
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Error: PyPDF2 not installed. Run: pip install PyPDF2")
    exit(1)

from backend.services.keyword_extractor import extract_keywords
from backend.services.resume_processor import (
    find_missing_keywords,
    inject_white_keywords,
)


def compile_latex_to_pdf(latex_content: str, output_path: Path) -> bool:
    """Compile LaTeX content to PDF using TinyTeX."""
    pdflatex_cmd = str(Path.home() / "Library/TinyTeX/bin/universal-darwin/pdflatex")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        tex_file = tmp_path / "resume.tex"
        pdf_file = tmp_path / "resume.pdf"
        
        tex_file.write_text(latex_content, encoding="utf-8")
        
        # Compile twice for proper formatting
        for _ in range(2):
            result = subprocess.run(
                [pdflatex_cmd, "-interaction=nonstopmode", 
                 "-output-directory", str(tmp_path), str(tex_file)],
                capture_output=True,
                timeout=30,
            )
        
        if pdf_file.exists():
            # Copy to output location
            import shutil
            shutil.copy(pdf_file, output_path)
            return True
        else:
            print("PDF compilation failed!")
            print(result.stdout[-500:] if result.stdout else "No output")
            return False


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from PDF."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def test_end_to_end():
    """Run end-to-end test."""
    print("=" * 70)
    print("END-TO-END KEYWORD INJECTION TEST")
    print("=" * 70)
    print()
    
    # Step 1: Read original resume
    resume_file = Path("main.tex")
    if not resume_file.exists():
        print(f"Error: {resume_file} not found!")
        return False
    
    resume_content = resume_file.read_text(encoding="utf-8")
    print(f"✓ Step 1: Loaded resume ({len(resume_content)} chars)")
    
    # Step 2: Sample job description
    job_description = """
    Senior Software Engineer - Full Stack
    
    We are looking for an experienced engineer with:
    - Strong proficiency in TypeScript, Node.js, and React
    - Experience with GraphQL APIs and microservices architecture
    - Familiarity with Terraform and infrastructure as code
    - Knowledge of Redis caching and PostgreSQL optimization
    - Experience with Kubernetes orchestration and Helm charts
    - Understanding of observability tools like Datadog or New Relic
    - Strong problem-solving skills and system design expertise
    - Experience with event-driven architectures using Kafka or RabbitMQ
    - Familiarity with CI/CD pipelines using GitHub Actions or GitLab CI
    - Experience mentoring junior developers and code reviews
    
    Bonus: Experience with serverless computing (AWS Lambda), 
    WebSockets for real-time features, and ElasticSearch.
    """
    
    print(f"✓ Step 2: Sample job description loaded")
    
    # Step 3: Extract keywords
    keywords = extract_keywords(job_description, max_keywords=30)
    print(f"✓ Step 3: Extracted {len(keywords)} keywords")
    print(f"   Top 10: {', '.join(keywords[:10])}")
    print()
    
    # Step 4: Find missing keywords
    missing_keywords = find_missing_keywords(resume_content, keywords)
    print(f"✓ Step 4: Found {len(missing_keywords)} missing keywords")
    print(f"   Missing: {', '.join(missing_keywords[:10])}")
    print()
    
    if not missing_keywords:
        print("⚠️  No missing keywords - resume already contains all keywords!")
        print("   Using first 10 keywords for testing anyway...")
        missing_keywords = keywords[:10]
    
    # Step 5: Inject keywords into resume
    updated_resume, modified, warnings = inject_white_keywords(
        resume_content, missing_keywords
    )
    print(f"✓ Step 5: Injected keywords into resume")
    print(f"   Modified: {modified}")
    if warnings:
        print(f"   Warnings: {warnings}")
    print()
    
    # Step 6: Compile to PDF
    output_pdf = Path("test_with_keywords.pdf")
    print(f"✓ Step 6: Compiling LaTeX to PDF...")
    if not compile_latex_to_pdf(updated_resume, output_pdf):
        print("❌ PDF compilation failed!")
        return False
    print(f"   PDF saved: {output_pdf} ({output_pdf.stat().st_size} bytes)")
    print()
    
    # Step 7: Extract text from PDF
    print(f"✓ Step 7: Extracting text from PDF...")
    pdf_text = extract_text_from_pdf(output_pdf)
    pdf_text_lower = pdf_text.lower()
    print(f"   Extracted {len(pdf_text)} characters")
    print()
    
    # Step 8: Verify keywords in PDF
    print(f"✓ Step 8: Verifying keywords in PDF...")
    found = []
    missing = []
    
    for keyword in missing_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in pdf_text_lower:
            found.append(keyword)
        else:
            missing.append(keyword)
    
    print()
    print("=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)
    print(f"Total Keywords Injected: {len(missing_keywords)}")
    print(f"✅ Found in PDF: {len(found)} ({len(found)/len(missing_keywords)*100:.1f}%)")
    print(f"❌ Missing from PDF: {len(missing)} ({len(missing)/len(missing_keywords)*100:.1f}%)")
    print()
    
    if found:
        print("✅ FOUND KEYWORDS:")
        for i, kw in enumerate(found, 1):
            print(f"  {i}. {kw}")
        print()
    
    if missing:
        print("❌ MISSING KEYWORDS:")
        for i, kw in enumerate(missing, 1):
            print(f"  {i}. {kw}")
        print()
    
    print("=" * 70)
    
    # Check for white text block in LaTeX
    if "\\color{white}" in updated_resume:
        print("✅ White text block found in LaTeX")
    else:
        print("⚠️  Warning: No white text block in LaTeX")
    
    print()
    
    # Final verdict
    if len(missing) == 0:
        print("🎉 SUCCESS: All injected keywords found in PDF!")
        print(f"   PDF saved as: {output_pdf}")
        return True
    elif len(found) / len(missing_keywords) >= 0.8:
        print("⚠️  PARTIAL SUCCESS: Most keywords found")
        return True
    else:
        print("❌ FAILURE: Many keywords missing from PDF")
        return False


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    success = test_end_to_end()
    sys.exit(0 if success else 1)

