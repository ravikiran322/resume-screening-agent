# Resume Screening AI Agent

An automated, end-to-end Python application that screens, ranks, and explains candidates' relevance to a Job Description (JD) using Natural Language Processing (NLP). Built with a modern Streamlit interface, the application processes resumes in **PDF, DOCX, and TXT** formats.

---

## 🛠️ Tech Stack & Key Libraries

- **Python 3.11**
- **Streamlit** (Interactive Dashboard UI)
- **pdfplumber** (High-fidelity text extraction from PDF resumes)
- **python-docx** (Structured text extraction from DOCX resumes)
- **scikit-learn** (TF-IDF Vectorization & Cosine Similarity)
- **pandas** & **numpy** (Structured data manipulation and analysis)
- **reportlab** (Optional, used for mock data generation)

---

## 📂 Project Structure

```text
resume-screening-agent/
│
├── app.py                      # Main Streamlit dashboard application
├── requirements.txt            # Python dependencies list
├── README.md                   # Project documentation
├── generate_mock_resumes.py    # Test data generator (PDF, DOCX, TXT formats)
│
├── data/
│   ├── jd.txt                  # Sample Job Description text
│   └── resumes/                # Directory containing candidate resumes
│
├── output/                     # Export directory (CSV & JSON format exports)
│
└── utils/
    ├── pdf_parser.py           # Extracts raw text from PDF files using pdfplumber
    ├── docx_parser.py          # Extracts text from paragraphs and tables in DOCX files
    ├── skill_extractor.py      # Rule-based skill taxonomies mapping and matching
    ├── experience_extractor.py # Regex heuristics for Name, Education, and Experience
    └── scorer.py               # TF-IDF, Cosine Similarity, and Explanation engine
```

---

## ⚙️ Installation & Setup

1. **Clone or Navigate to the Directory**:
   Ensure you are in the project folder `resume-screening-agent`.

2. **Set up a Virtual Environment** (Recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Generate Test Resumes** (Generates 10 mock candidates):
   To generate a diverse set of 10 resumes (mix of PDF, DOCX, and TXT formats representing high, medium, and low matches), run:
   ```bash
   python generate_mock_resumes.py
   ```

---

## 🚀 Running the Application

Launch the Streamlit web dashboard:
```bash
streamlit run app.py
```

The application will open automatically in your browser (usually at `http://localhost:8501`).

---

## 🧠 How Each Module Works

### 1. Document Parsing (`utils/pdf_parser.py` and `utils/docx_parser.py`)
- **PDF Parser**: Uses `pdfplumber` to open and extract page-by-page text. It handles multi-page resumes and contains exception-handling guards to log corrupted files.
- **DOCX Parser**: Uses `python-docx` to extract text from standard paragraphs and tabular cells. Cell extraction is structured with cell separators (`|`) to maintain visual layout information.

### 2. Extractor Heuristics (`utils/experience_extractor.py` and `utils/skill_extractor.py`)
- **Name Extraction**: Analyzes the first 8 lines of text. It ignores contact headers, links (like GitHub/LinkedIn), and emails, using a capitalization check to return the candidate's name. It falls back to formatting the filename if text parsing is insufficient.
- **Education Extraction**: Scans the text for degree indicators (e.g., Bachelor, Master, PhD, B.Tech, M.S., MBA) and institution terms (University, College). It returns a deduplicated list of the top 3 academic highlights.
- **Experience Extraction**: 
  1. Searches for direct experience declarations (e.g., "5+ years of experience").
  2. Fallback: Extracts year ranges (e.g., `2018 - 2021` or `2020 - Present`), sorts them, merges overlapping periods (so concurrent jobs do not inflate experience), and calculates total work duration.
- **Skill Extraction**: Matches words against a defined taxonomy dictionary (Languages, Frameworks, Databases, DevOps, Domains, Soft Skills) utilizing word boundary regex (`\b(skill)\b`) to prevent partial matches.

### 3. Relevance Engine & Explanation (`utils/scorer.py`)
- **Scoring**: Standardizes the Job Description and Resume text using a TF-IDF (Term Frequency-Inverse Document Frequency) Vectorizer, filtering out English stopwords. It then calculates the Cosine Similarity between the vectors, expressing the result as a percentage score (0% to 100%).
- **Explanations**: Evaluates the intersection of the candidate's skills against those in the Job Description. It constructs a conversational explanation detailing the number of matched skills, displaying highlights (e.g., "Matched 6 out of 8 required skills including Python, SQL..."), listing missing prerequisites, and grading overall textual compatibility.

### 4. Interactive Dashboard (`app.py`)
- Streamlines the candidate selection workflow.
- Features metric widgets summarizing key screening benchmarks.
- Lists all candidates in a sorted ranking table featuring custom progress bars representing relevance.
- Offers direct single-candidate profile drill-down tabs (AI Explanation, Profile Breakdown, and Raw Resume Text).
- Includes instant downloads for JSON and CSV exports.

---

## 🔮 Future Enhancements & Recommendations

If more development time were available, the following improvements could be added:
1. **Semantic NLP Embeddings**: Replace or augment TF-IDF with pre-trained sentence transformer embeddings (e.g., HuggingFace models like `all-MiniLM-L6-v2`) to capture context synonyms (e.g., matching "Deep Learning" to "Neural Networks" or "AWS" to "Amazon Web Services").
2. **LLM Explanations**: Integrate a lightweight, local LLM (e.g., Llama 3 via Ollama) or an API (e.g., Google Gemini API) to generate highly personalized candidate summaries, career highlights, and specific interview questions.
3. **Contact Parsing**: Add regex extractions for Email Address and Phone Numbers, showing them in the table and allowing hiring managers to email or call directly from the dashboard.
4. **Keyword Customization**: Provide an interface in Streamlit to customize the skill taxonomies or add custom mandatory skills that candidates must have to avoid being filtered.
