#!/usr/bin/env python3
"""
Demonstration: How ATS Systems Detect White/Hidden Keywords

This script shows that while white keywords are invisible to human eyes,
they are fully visible to ATS systems that extract text from PDFs.
"""
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Please install: pip install PyPDF2")
    exit(1)


def simulate_ats_extraction(pdf_path: Path) -> dict:
    """
    Simulate how an ATS system extracts and analyzes a PDF resume.
    
    ATS systems:
    1. Extract ALL text from PDF (ignoring colors, fonts, sizes)
    2. Tokenize and normalize the text
    3. Match against job description keywords
    4. Score based on keyword presence and frequency
    """
    print("=" * 80)
    print("SIMULATING ATS (Applicant Tracking System) TEXT EXTRACTION")
    print("=" * 80)
    print()
    
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        return {}
    
    # Step 1: Extract all text (this is what ATS does)
    print("Step 1: Extracting ALL text from PDF (including white/hidden text)...")
    reader = PdfReader(pdf_path)
    full_text = ""
    for page_num, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        full_text += page_text + "\n"
        print(f"  Page {page_num}: {len(page_text)} characters extracted")
    
    print(f"\n  Total text extracted: {len(full_text)} characters")
    print()
    
    # Step 2: Show where white keywords appear
    print("Step 2: Locating hidden keyword section...")
    
    # Find the white keyword section
    lines = full_text.split('\n')
    keyword_section_start = -1
    for i, line in enumerate(lines):
        # Hidden keywords typically appear at the end or as a block
        if any(indicator in line.lower() for indicator in ['terraform', 'graphql', 'redis', 'kafka']):
            # Check if this is a dense keyword block (multiple keywords in one line)
            keyword_count = sum(1 for kw in ['typescript', 'graphql', 'terraform', 'redis', 'kubernetes', 'kafka'] 
                              if kw in line.lower())
            if keyword_count >= 3:  # Likely a keyword block
                keyword_section_start = i
                print(f"  ✓ Found hidden keyword section at line {i}")
                print(f"  Content: {line[:100]}...")
                break
    
    print()
    
    # Step 3: Extract and normalize keywords (ATS approach)
    print("Step 3: Tokenizing text into keywords (ATS normalization)...")
    
    # Simple tokenization (real ATS is more sophisticated)
    import re
    tokens = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#\-\.]{1,}\b', full_text.lower())
    unique_keywords = set(tokens)
    
    print(f"  Total tokens: {len(tokens)}")
    print(f"  Unique keywords: {len(unique_keywords)}")
    print()
    
    # Step 4: Check for specific job-related keywords
    print("Step 4: Checking for job-specific keywords...")
    
    target_keywords = [
        'typescript', 'graphql', 'terraform', 'redis', 'kubernetes',
        'kafka', 'rabbitmq', 'microservices', 'serverless', 'datadog',
        'postgresql', 'elasticsearch', 'websockets', 'observability'
    ]
    
    found_keywords = []
    missing_keywords = []
    
    for kw in target_keywords:
        if kw in full_text.lower():
            found_keywords.append(kw)
        else:
            missing_keywords.append(kw)
    
    print(f"  ✅ Found: {len(found_keywords)}/{len(target_keywords)} keywords")
    print(f"  ❌ Missing: {len(missing_keywords)}/{len(target_keywords)} keywords")
    print()
    
    if found_keywords:
        print("  Keywords detected by ATS:")
        for i, kw in enumerate(found_keywords, 1):
            # Count occurrences
            count = full_text.lower().count(kw)
            print(f"    {i:2}. {kw:<20} (appears {count} time{'s' if count > 1 else ''})")
    
    print()
    
    # Step 5: ATS Scoring simulation
    print("Step 5: Simulated ATS Scoring...")
    
    keyword_match_score = (len(found_keywords) / len(target_keywords)) * 100
    
    print(f"  Keyword Match Score: {keyword_match_score:.1f}%")
    
    if keyword_match_score >= 80:
        print(f"  Rating: ⭐⭐⭐⭐⭐ EXCELLENT - Strong match for position")
    elif keyword_match_score >= 60:
        print(f"  Rating: ⭐⭐⭐⭐ GOOD - Competitive candidate")
    elif keyword_match_score >= 40:
        print(f"  Rating: ⭐⭐⭐ MODERATE - Consider for review")
    else:
        print(f"  Rating: ⭐⭐ LOW - May not meet requirements")
    
    print()
    print("=" * 80)
    print()
    
    return {
        'total_text_length': len(full_text),
        'found_keywords': found_keywords,
        'missing_keywords': missing_keywords,
        'match_score': keyword_match_score,
    }


def compare_before_after():
    """Compare ATS detection before and after keyword injection."""
    print("\n" + "=" * 80)
    print("COMPARISON: ATS Detection Before vs. After Keyword Injection")
    print("=" * 80)
    print()
    
    original_pdf = Path("main.pdf")
    updated_pdf = Path("test_with_keywords.pdf")
    
    if original_pdf.exists():
        print("📄 ORIGINAL PDF (without hidden keywords):")
        print("-" * 80)
        original_results = simulate_ats_extraction(original_pdf)
        
    if updated_pdf.exists():
        print("\n📄 UPDATED PDF (with hidden keywords):")
        print("-" * 80)
        updated_results = simulate_ats_extraction(updated_pdf)
        
        if original_pdf.exists():
            print("\n📊 IMPROVEMENT SUMMARY:")
            print("=" * 80)
            original_score = original_results.get('match_score', 0)
            updated_score = updated_results.get('match_score', 0)
            improvement = updated_score - original_score
            
            print(f"  Original ATS Score: {original_score:.1f}%")
            print(f"  Updated ATS Score:  {updated_score:.1f}%")
            print(f"  Improvement:        +{improvement:.1f} percentage points")
            print()
            
            new_keywords = set(updated_results.get('found_keywords', [])) - set(original_results.get('found_keywords', []))
            if new_keywords:
                print(f"  ✨ New keywords detected by ATS: {', '.join(sorted(new_keywords))}")
            print()
            print("=" * 80)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║  ATS KEYWORD DETECTION DEMONSTRATION                                       ║
║                                                                            ║
║  This demonstrates how ATS (Applicant Tracking Systems) detect keywords   ║
║  in PDFs, including "white" (invisible) text that humans cannot see.      ║
║                                                                            ║
║  KEY INSIGHT: ATS systems extract ALL text from PDFs regardless of color, ║
║  font size, or visibility. White text is just as readable to ATS as       ║
║  black text - only humans can't see it!                                   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    compare_before_after()
    
    print("\n✅ CONCLUSION:")
    print("   White/hidden keywords are FULLY DETECTABLE by ATS systems.")
    print("   They boost your keyword match score without cluttering the visible resume.")
    print()

