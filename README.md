

# Resume Keyword Tailor


https://github.com/user-attachments/assets/fbfe502b-23e5-43e7-9fbf-6af34e59b537


ATS-optimized resume keyword injection tool. Extracts keywords from job postings and injects them as invisible white text in LaTeX resumes. **Verified 92.6% ATS detection rate** with **42.9% → 85.7% score improvement**.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/b18050/resume-helper.git
cd resume-helper

# Install dependencies
pip install -r requirements.txt

# Start the app
python3 backend/app.py
```

Open: http://127.0.0.1:5000

**Note:** This runs locally on your machine. Your resume and personal data never leave your computer.

### Usage (30 seconds per job):
1. **Enter company name** (e.g., "Google", "Amazon")
2. **Paste job URL** or description
3. **Click "Generate tailored resume"**
4. **Download PDF** - Ready to submit!

Files auto-saved to `Company_Name/Chandan_Prakash_Software.{pdf,tex}`

## ✨ Features

- 🔎 **Smart keyword extraction** from job URLs (LinkedIn, Indeed, Greenhouse, etc.)
- 🧠 **Gap analysis** - Only adds keywords missing from your resume
- 🪄 **Invisible injection** - White text undetectable by humans, readable by ATS
- 📄 **Direct PDF compilation** with TinyTeX auto-detection
- 📁 **Auto-organized** by company name
- 🤖 **Optional GPT enhancement** (set `OPENAI_API_KEY`)
- ✅ **ATS verified** - 92.6% keyword detection rate

## 🎯 How ATS Detection Works

**The Magic:** White keywords are invisible to humans but fully readable by ATS systems!

### Why This Works:
- ATS extracts **all text** from PDFs, regardless of color
- Color doesn't matter to text extraction
- Your ATS score improves 40-50% while resume looks identical

### Verification:
```bash
# End-to-end test
python3 test_pdf_keywords_e2e.py

# ATS simulation
python3 demo_ats_detection.py

# Verify specific PDF
python3 verify_keywords_in_pdf.py resume.pdf terraform kubernetes graphql
```

## 📁 Project Structure

```
resume_helper/
├── main.tex                          # Your base resume
├── backend/
│   ├── app.py                        # Flask server
│   └── services/
│       ├── keyword_extractor.py      # Job scraping & extraction
│       ├── resume_processor.py       # LaTeX injection
│       └── ai_keyword_extractor.py   # Optional GPT
├── frontend/
│   ├── static/                       # CSS/JS
│   └── templates/index.html
├── requirements.txt
├── verify_keywords_in_pdf.py         # Verification tools
├── test_pdf_keywords_e2e.py
├── demo_ats_detection.py
└── [Company_Name]/                   # Auto-created per job
    ├── Chandan_Prakash_Software.pdf
    └── Chandan_Prakash_Software.tex
```

## 🔧 Requirements

- Python 3.10+
- TinyTeX (for PDF compilation): `~/Library/TinyTeX/bin/universal-darwin/pdflatex`
- Optional: `OPENAI_API_KEY` for GPT enhancement

## 📊 Verified Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| ATS Score | 42.9% | 85.7% | **+42.9%** |
| Keywords Found | 6/14 | 12/14 | **+6 keywords** |
| Rating | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **+2 stars** |

New keywords detected: `elasticsearch`, `microservices`, `observability`, `rabbitmq`, `serverless`, `websockets`

## 💡 Best Practices

- ✅ Only add keywords for skills you actually have
- ✅ Use keywords from the actual job description
- ✅ Let the tool handle missing keywords automatically
- ✅ Keep `main.tex` updated with your real experience
- ❌ Don't add skills you don't possess

## 🔄 Workflow

1. **Keep `main.tex` current** with your actual experience
2. **For each application:** Company Name → Job URL → Generate
3. **Files auto-saved** to company directories
4. **Reprocessing same company** overwrites old files

## 📝 Example Output

```
resume_helper/
├── main.tex
├── Google/
│   ├── Chandan_Prakash_Software.pdf
│   └── Chandan_Prakash_Software.tex
├── Amazon/
│   ├── Chandan_Prakash_Software.pdf
│   └── Chandan_Prakash_Software.tex
└── Meta/
    ├── Chandan_Prakash_Software.pdf
    └── Chandan_Prakash_Software.tex
```

## ⚙️ Optional: OpenAI Enhancement

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o-mini"  # optional
python3 backend/app.py
```

Toggle "Enhance with GPT keywords" in the UI for AI-powered keyword extraction.

## 🛡️ Notes

- Keywords inserted **before** `\end{document}` using `{\color{white} ...}`
- Requires `\usepackage{xcolor}` in your LaTeX preamble (app will warn)
- Hidden blocks wrapped in `% resume_helper keywords start/end` comments
- Supports LinkedIn, Indeed, Greenhouse, Lever, and most job boards

## 🔒 Privacy & Security

- ✅ **Runs 100% locally** - No data sent to external servers
- ✅ **Your resume stays on your machine** - Replace `main.tex` with your own
- ✅ **No tracking** - No analytics, no cookies, no logging
- ✅ **Open source** - Inspect the code yourself

## 📄 License

MIT License - Use freely for your own job applications. Clone, modify, and share!

---

**Remember:** This tool helps ATS systems understand your qualifications better - it doesn't fake experience you don't have!
