#!/usr/bin/env python3
"""
Script to verify that hidden keywords are present in the compiled PDF.
This extracts text from a PDF and checks for the presence of keywords.
"""
import sys
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Error: PyPDF2 not installed. Run: pip install PyPDF2")
    sys.exit(1)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text content from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""


def verify_keywords_in_pdf(pdf_path: Path, keywords: list[str]) -> dict:
    """
    Verify which keywords are present in the PDF.
    
    Returns:
        dict with 'found', 'missing', 'total', and 'pdf_text_preview' keys
    """
    if not pdf_path.exists():
        return {
            "error": f"PDF file not found: {pdf_path}",
            "found": [],
            "missing": keywords,
            "total": len(keywords),
        }
    
    pdf_text = extract_text_from_pdf(pdf_path)
    pdf_text_lower = pdf_text.lower()
    
    found = []
    missing = []
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in pdf_text_lower:
            found.append(keyword)
        else:
            missing.append(keyword)
    
    return {
        "found": found,
        "missing": missing,
        "total": len(keywords),
        "pdf_text_preview": pdf_text[:500],  # First 500 chars for inspection
        "pdf_text_length": len(pdf_text),
    }


def print_verification_report(result: dict, pdf_path: Path):
    """Print a formatted verification report."""
    print("=" * 70)
    print(f"PDF KEYWORD VERIFICATION REPORT")
    print("=" * 70)
    print(f"PDF File: {pdf_path}")
    print(f"PDF Text Length: {result.get('pdf_text_length', 0)} characters")
    print()
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    total = result['total']
    found_count = len(result['found'])
    missing_count = len(result['missing'])
    
    print(f"Total Keywords to Check: {total}")
    print(f"✅ Found in PDF: {found_count} ({found_count/total*100:.1f}%)")
    print(f"❌ Missing from PDF: {missing_count} ({missing_count/total*100:.1f}%)")
    print()
    
    if result['found']:
        print("✅ FOUND KEYWORDS:")
        for i, kw in enumerate(result['found'][:20], 1):  # Show first 20
            print(f"  {i}. {kw}")
        if len(result['found']) > 20:
            print(f"  ... and {len(result['found']) - 20} more")
        print()
    
    if result['missing']:
        print("❌ MISSING KEYWORDS:")
        for i, kw in enumerate(result['missing'][:20], 1):  # Show first 20
            print(f"  {i}. {kw}")
        if len(result['missing']) > 20:
            print(f"  ... and {len(result['missing']) - 20} more")
        print()
    
    print("=" * 70)
    
    # Success criteria
    if missing_count == 0:
        print("🎉 SUCCESS: All keywords found in PDF!")
    elif found_count / total >= 0.8:
        print("⚠️  WARNING: Most keywords found, but some are missing.")
    else:
        print("❌ FAILURE: Many keywords are missing from the PDF.")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_keywords_in_pdf.py <pdf_file> [keyword1] [keyword2] ...")
        print("\nExample:")
        print("  python verify_keywords_in_pdf.py resume.pdf python javascript kubernetes")
        print("\nOr test with your existing PDF:")
        print("  python verify_keywords_in_pdf.py Chandan_Prakash_Software.pdf")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    
    if len(sys.argv) > 2:
        # Keywords provided as arguments
        keywords = sys.argv[2:]
    else:
        # Use some sample keywords for testing
        keywords = [
            "Python", "Java", "JavaScript", "React", "AWS",
            "Docker", "Kubernetes", "MongoDB", "REST", "APIs",
            "Machine Learning", "Deep Learning", "Git", "CI/CD"
        ]
        print(f"No keywords provided, using sample keywords for testing.")
        print()
    
    result = verify_keywords_in_pdf(pdf_path, keywords)
    print_verification_report(result, pdf_path)

