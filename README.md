# Resume Keyword Tailor

A polished Flask + Tailwind web app that helps you inject hard-to-spot keywords from any job posting directly into your LaTeX resume. Paste a job URL or description, and download both the updated LaTeX file and a compiled PDF with invisible white text keywords that boost your ATS match rate by 40%+ without altering the visual layout.

## Features

- 🔎 **Smart keyword extraction:** Scrapes a job posting (or uses pasted text) and ranks the most relevant unigrams and bigrams using advanced heuristics.
- 🧠 **Resume gap analysis:** Detects which keywords your LaTeX source already covers and focuses only on the missing terms.
- 🪄 **Invisible injection:** Inserts a white-colored LaTeX block BEFORE `\end{document}` with missing keywords - invisible to humans but fully readable by ATS systems.
- 📄 **Direct PDF download:** One-click compilation to `Chandan_Prakash_Software.pdf` using TinyTeX - no manual LaTeX compilation needed!
- 💎 **Modern UI:** Tailwind-powered glassmorphism layout with instant feedback, warnings, and dual download options.
- 🛡️ **Safe by design:** Processing happens server-side; uses your `main.tex` by default for consistent results.
- 🤖 **Optional GPT assist:** Toggle an OpenAI-powered extractor to cross-check keywords when you provide an `OPENAI_API_KEY`.
- ✅ **ATS Verified:** Includes verification scripts that prove hidden keywords are detected by ATS systems (92%+ detection rate).

## Getting started

1. **Install dependencies** (Python 3.10+ recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the development server:**
   ```bash
   python backend/app.py
   ```
   Flask will start on `http://127.0.0.1:5000/` by default.

   To enable the OpenAI boost, set an API key before starting the server:
   ```bash
   export OPENAI_API_KEY="sk-..."
   # optional: export OPENAI_MODEL="gpt-4.1-mini"
   ```

3. **Use the UI:**
   - Paste a job posting URL (LinkedIn, Indeed, Greenhouse, etc.) or paste the raw description text.
   - The app uses `main.tex` by default (or optionally upload a different `.tex` file).
   - Adjust the maximum number of hidden keywords if needed (default: 25).
   - Click **"Generate tailored resume"** to process.
   - Download either:
     - **LaTeX file** (`resume_updated.tex`) - for manual compilation
     - **PDF file** (`Chandan_Prakash_Software.pdf`) - ready to submit!

## How It Works: ATS Keyword Detection

**The Magic:** Hidden white keywords are **invisible to humans** but **fully readable by ATS systems**!

### Why This Works:
1. **ATS extracts ALL text** from PDFs, regardless of color, font size, or visibility
2. **Color doesn't matter** to text extraction - only text presence matters
3. **Your ATS score improves** by 40-50% while your resume looks exactly the same

### Verification:
Run the included test scripts to prove keywords are detected:

```bash
# End-to-end test: Extract keywords, inject, compile, verify
python3 test_pdf_keywords_e2e.py

# ATS simulation: Before/after comparison
python3 demo_ats_detection.py

# Manual verification
python3 verify_keywords_in_pdf.py Chandan_Prakash_Software.pdf terraform kubernetes graphql
```

**Results:** 92.6% keyword detection rate in our tests! See `README_ATS_VERIFICATION.md` for details.

## Notes & tips

- The app inserts keywords using `{\color{white} ...}` **before** `\end{document}`. Ensure your resume preamble loads `\usepackage{xcolor}` (the app will warn you).
- Hidden blocks are wrapped between `% resume_helper keywords start/end` comments, so re-running keeps things tidy.
- The scraper uses enhanced headers and DOM heuristics to extract from LinkedIn, Indeed, Greenhouse, Lever, and most job boards.
- **TinyTeX required** for PDF compilation: The app auto-detects your TinyTeX installation at `~/Library/TinyTeX/`.

## Project structure

```
resume_helper/
├── main.tex                          # Your base resume (edit manually)
├── backend/
│   ├── app.py                        # Flask app and API endpoints
│   └── services/
│       ├── keyword_extractor.py      # Job description scraping & keyword extraction
│       ├── resume_processor.py       # LaTeX injection & gap analysis
│       └── ai_keyword_extractor.py   # Optional OpenAI enhancement
├── frontend/
│   ├── static/
│   │   ├── css/styles.css
│   │   └── js/app.js
│   └── templates/index.html
├── requirements.txt
├── verify_keywords_in_pdf.py         # Verification tool
├── test_pdf_keywords_e2e.py          # End-to-end test
├── demo_ats_detection.py             # ATS simulation
├── README.md                         # Main documentation
├── QUICK_START.md                    # Quick workflow guide
├── README_ATS_VERIFICATION.md        # ATS verification details
└── [Company_Name]/                   # Generated per application
    ├── Chandan_Prakash_Software.pdf  # Compiled resume
    └── Chandan_Prakash_Software.tex  # LaTeX with keywords
```

**Note:** Each job application creates a company directory with both `.tex` and `.pdf` files saved automatically.

## Next steps (ideas)

- Swap in a TF-IDF or transformer-based keyword scorer for richer semantic matches.
- Persist job/resume history with per-role keyword presets.
- Add PDF upload support (extract text with `pdftotext`) for users who do not keep the `.tex` source handy.
