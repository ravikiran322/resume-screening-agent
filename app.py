import streamlit as st
import pandas as pd
import json
import os
from typing import List, Dict, Any

# Import utilities
from utils.pdf_parser import extract_text_from_pdf
from utils.docx_parser import extract_text_from_docx
from utils.skill_extractor import extract_skills, get_flat_skills
from utils.experience_extractor import extract_name, extract_education, extract_experience
from utils.scorer import calculate_similarity_score, generate_explanation

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Resume Screening AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Custom CSS Injector for modern look
st.markdown("""
<style>
    /* Gradient headers and custom fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-title {
        font-size: 3rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #6B7280;
        margin-bottom: 25px;
    }
    
    /* Glassmorphism Card styling */
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.03);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        margin-bottom: 20px;
    }
    
    .dark-card {
        background: #0F172A;
        color: #F8FAFC;
        border-radius: 12px;
        padding: 20px;
        border-left: 5px solid #6366F1;
        margin-bottom: 15px;
    }
    
    /* Metrics panel */
    .metric-box {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        border: 1px solid #334155;
        color: white;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #818CF8;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    
    .badge-primary { background-color: #E0E7FF; color: #4338CA; }
    .badge-success { background-color: #D1FAE5; color: #065F46; }
    .badge-warning { background-color: #FEF3C7; color: #92400E; }
    .badge-secondary { background-color: #F3F4F6; color: #374151; }
</style>
""", unsafe_allow_html=True)

# Helper function to read file contents
def read_text_file(path: str) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def process_resume(file_name: str, file_bytes: bytes, file_ext: str, jd_text: str) -> Dict[str, Any]:
    """
    Parses and processes a single resume, extracting details and calculating similarity.
    """
    # Write temp file to read since pdfplumber and python-docx require file paths or file-like objects
    temp_dir = os.path.join(".gemini", "temp") if ".gemini" in os.listdir() else "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file_name)
    
    with open(temp_path, "wb") as f:
        f.write(file_bytes)
        
    text = ""
    try:
        # Extract text based on file format
        if file_ext.lower() == ".pdf":
            text = extract_text_from_pdf(temp_path)
        elif file_ext.lower() == ".docx":
            text = extract_text_from_docx(temp_path)
        else: # .txt
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = file_bytes.decode("latin-1")
    except Exception as e:
        st.error(f"Error parsing {file_name}: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    # If extraction yielded nothing, return empty record
    if not text.strip():
        return {
            "Filename": file_name,
            "Name": extract_name("", file_name),
            "Skills": [],
            "Education": ["Not found"],
            "Experience": 0.0,
            "Score": 0.0,
            "Explanation": "Failed to parse text from resume file.",
            "RawText": ""
        }
        
    # Extract details
    name = extract_name(text, file_name)
    skills_dict = extract_skills(text)
    flat_skills = get_flat_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)
    
    # Calculate similarity & explanations
    score = calculate_similarity_score(jd_text, text)
    explanation = generate_explanation(jd_text, text, score)
    
    # Get skill overlap count
    jd_skills = get_flat_skills(jd_text)
    matched_skills = flat_skills.intersection(jd_skills)
    
    # Reformat skills dict to list of strings
    skills_list = []
    for cat, sks in skills_dict.items():
        skills_list.extend(sks)
        
    return {
        "Filename": file_name,
        "Name": name,
        "Skills": list(set(skills_list)),
        "Education": education,
        "Experience": experience,
        "Score": score,
        "Explanation": explanation,
        "RawText": text,
        "SkillsMatchedCount": len(matched_skills),
        "TotalJDSkillsCount": len(jd_skills)
    }

# App Layout
st.markdown('<div class="main-title">🤖 Resume Screening AI Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Automated Ranker & Explainer powered by NLP (TF-IDF & Cosine Similarity)</div>', unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
st.sidebar.header("📁 Configuration Panel")

# JD Selection Source
jd_source = st.sidebar.radio("1. Job Description (JD) Source", ["Use Sample JD", "Upload Custom JD File", "Paste JD Text"])

jd_text = ""
if jd_source == "Use Sample JD":
    sample_jd_path = os.path.join("data", "jd.txt")
    if os.path.exists(sample_jd_path):
        jd_text = read_text_file(sample_jd_path)
        st.sidebar.success("Loaded default 'data/jd.txt'")
    else:
        st.sidebar.error("Sample 'data/jd.txt' not found. Please paste JD instead.")
elif jd_source == "Upload Custom JD File":
    uploaded_jd = st.sidebar.file_uploader("Upload Job Description (TXT)", type=["txt"])
    if uploaded_jd:
        jd_text = uploaded_jd.read().decode("utf-8")
        st.sidebar.success("Uploaded custom JD file.")
else:
    jd_text = st.sidebar.text_area("Paste Job Description Text", height=250)

# Display JD in sidebar expander
with st.sidebar.expander("🔍 View Active Job Description", expanded=False):
    if jd_text:
        st.text(jd_text)
    else:
        st.warning("No Job Description active.")

# Resume Selection Source
st.sidebar.markdown("---")
st.sidebar.header("📄 Resume Source")
resume_source = st.sidebar.radio("2. Resume Input Mode", ["Use 10 Mock Resumes (Default)", "Upload Custom Resumes"])

uploaded_resumes = []
if resume_source == "Use 10 Mock Resumes (Default)":
    mock_resumes_dir = os.path.join("data", "resumes")
    if os.path.exists(mock_resumes_dir):
        mock_files = [f for f in os.listdir(mock_resumes_dir) if f.lower().endswith(('.pdf', '.docx', '.txt'))]
        if len(mock_files) >= 10:
            st.sidebar.success(f"Found {len(mock_files)} mock resumes in 'data/resumes/'.")
        else:
            st.sidebar.warning(f"Only found {len(mock_files)} files in 'data/resumes/'. Run 'generate_mock_resumes.py' to generate all 10.")
    else:
        st.sidebar.error("Mock resumes folder 'data/resumes/' not found. Please upload resumes or run generator.")
else:
    uploaded_resumes = st.sidebar.file_uploader("Upload Resumes (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=True)

# ----------------- MAIN FLOW -----------------

if not jd_text.strip():
    st.info("💡 Please upload or enter a Job Description (JD) in the sidebar to start screening candidates.")
else:
    # Compile candidate list
    candidate_records = []
    
    with st.spinner("⏳ Parsing resumes and computing relevance scores..."):
        if resume_source == "Use 10 Mock Resumes (Default)":
            mock_resumes_dir = os.path.join("data", "resumes")
            if os.path.exists(mock_resumes_dir):
                mock_files = [f for f in os.listdir(mock_resumes_dir) if f.lower().endswith(('.pdf', '.docx', '.txt'))]
                for file_name in mock_files:
                    file_path = os.path.join(mock_resumes_dir, file_name)
                    _, ext = os.path.splitext(file_name)
                    try:
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()
                        record = process_resume(file_name, file_bytes, ext, jd_text)
                        candidate_records.append(record)
                    except Exception as e:
                        st.error(f"Error reading {file_name}: {str(e)}")
        else:
            # Custom uploaded resumes
            for uploaded_file in uploaded_resumes:
                _, ext = os.path.splitext(uploaded_file.name)
                file_bytes = uploaded_file.read()
                record = process_resume(uploaded_file.name, file_bytes, ext, jd_text)
                candidate_records.append(record)
                
    if not candidate_records:
        st.warning("⚠️ No resumes loaded or uploaded. Please select a resume input mode in the sidebar.")
    else:
        # Convert to DataFrame
        df_all = pd.DataFrame(candidate_records)
        
        # Sort candidates by Score (highest to lowest)
        df_all = df_all.sort_values(by="Score", ascending=False).reset_index(drop=True)
        # Add Rank
        df_all.insert(0, "Rank", range(1, len(df_all) + 1))
        
        # ----------------- METRICS PANEL -----------------
        total_resumes = len(df_all)
        top_candidate = df_all.iloc[0]["Name"]
        top_score = df_all.iloc[0]["Score"]
        avg_score = round(df_all["Score"].mean(), 1)
        shortlisted = len(df_all[df_all["Score"] >= 50.0])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{total_resumes}</div>
                <div class="metric-label">Parsed Resumes</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{top_score}%</div>
                <div class="metric-label">Top Relevance Score</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{avg_score}%</div>
                <div class="metric-label">Average Match Score</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{shortlisted} / {total_resumes}</div>
                <div class="metric-label">Strong Matches (≥50%)</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")
        st.write("")
        
        # ----------------- EXPORT TRIGGER & OPTIONS -----------------
        col_title, col_export = st.columns([3, 1])
        with col_title:
            st.subheader("📊 Candidate Screening Rankings")
        with col_export:
            # Prepare export formats
            export_df = df_all.drop(columns=["RawText"])
            
            # CSV export
            csv_data = export_df.to_csv(index=False)
            
            # JSON export
            json_dict = export_df.to_dict(orient="records")
            json_data = json.dumps(json_dict, indent=4)
            
            # Show download buttons side-by-side
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                st.download_button(
                    label="📥 CSV",
                    data=csv_data,
                    file_name="resume_screen_results.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with exp_col2:
                st.download_button(
                    label="📥 JSON",
                    data=json_data,
                    file_name="resume_screen_results.json",
                    mime="application/json",
                    use_container_width=True
                )
                
        # ----------------- DISPLAY INTERACTIVE TABLE -----------------
        # For rendering, clean up list/columns to display cleanly
        display_df = df_all.copy()
        
        # Format columns for display
        display_df["Experience (Years)"] = display_df["Experience"].apply(lambda x: f"{x} Yrs" if x > 0 else "0 Yrs")
        display_df["Top Education"] = display_df["Education"].apply(lambda x: x[0] if x else "N/A")
        display_df["Skills Overlap"] = display_df.apply(
            lambda r: f"{r['SkillsMatchedCount']} / {r['TotalJDSkillsCount']} skills", axis=1
        )
        
        table_df = display_df[["Rank", "Name", "Score", "Experience (Years)", "Top Education", "Skills Overlap", "Filename"]]
        table_df = table_df.rename(columns={"Score": "Similarity Score"})
        
        st.dataframe(
            table_df,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", format="%d", width="small"),
                "Name": st.column_config.TextColumn("Candidate Name"),
                "Similarity Score": st.column_config.ProgressColumn(
                    "Relevance Score",
                    help="TF-IDF & Cosine Similarity Score",
                    format="%.2f%%",
                    min_value=0.0,
                    max_value=100.0
                ),
                "Experience (Years)": st.column_config.TextColumn("Experience"),
                "Top Education": st.column_config.TextColumn("Education"),
                "Skills Overlap": st.column_config.TextColumn("Skills Overlap"),
                "Filename": st.column_config.TextColumn("Source File")
            },
            use_container_width=True,
            hide_index=True
        )
        
        st.write("")
        st.write("")
        
        # ----------------- DETAILED CANDIDATE EVALUATION -----------------
        st.subheader("🔍 Detailed Candidate Profile Drill-Down")
        
        selected_candidate_name = st.selectbox(
            "Select a candidate to review detailed scoring and profile details:",
            options=df_all["Name"].tolist()
        )
        
        # Get selected candidate details
        candidate = df_all[df_all["Name"] == selected_candidate_name].iloc[0]
        
        # Render candidate profile card
        st.markdown(f"""
        <div class="dark-card">
            <h2 style="margin: 0; color: #818CF8;">{candidate['Name']}</h2>
            <p style="margin: 5px 0 15px 0; color: #94A3B8; font-size: 1.1rem;">Rank: #{candidate['Rank']} | File: {candidate['Filename']}</p>
            <div style="margin-bottom: 10px;">
                <span style="font-weight: 600; color: #F8FAFC;">Relevance Score:</span>
                <span style="color: #38BDF8; font-weight: 800; font-size: 1.2rem;">{candidate['Score']}%</span>
            </div>
            <div>
                <span style="font-weight: 600; color: #F8FAFC;">Total Experience:</span>
                <span style="color: #FBBF24; font-weight: 800; font-size: 1.2rem;">{candidate['Experience']} Years</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Detailed tabs
        tab_ai, tab_profile, tab_resume = st.tabs(["💡 AI Score Explanation", "👤 Profile Breakdown", "📄 Raw Resume Text"])
        
        with tab_ai:
            st.markdown("### Relevance Scoring Summary")
            st.info(candidate["Explanation"])
            
            # Show skill analysis
            st.write("")
            st.markdown("#### Skill Match Overview")
            
            # Extract candidate skills vs JD skills
            jd_skills_flat = get_flat_skills(jd_text)
            c_skills_flat = set([s.lower() for s in candidate["Skills"]])
            
            matched_s = c_skills_flat.intersection(jd_skills_flat)
            missing_s = jd_skills_flat - c_skills_flat
            extra_s = c_skills_flat - jd_skills_flat
            
            col_match, col_miss, col_extra = st.columns(3)
            
            with col_match:
                st.markdown(f"**Matched Required Skills ({len(matched_s)})**")
                if matched_s:
                    for s in sorted(list(matched_s)):
                        st.markdown(f'<span class="badge badge-success">{s.upper() if s in ["aws", "gcp", "sql", "api", "nlp", "ci/cd", "db"] else s.title()}</span>', unsafe_allow_html=True)
                else:
                    st.write("None")
                    
            with col_miss:
                st.markdown(f"**Missing Required Skills ({len(missing_s)})**")
                if missing_s:
                    for s in sorted(list(missing_s)):
                        st.markdown(f'<span class="badge badge-warning">{s.upper() if s in ["aws", "gcp", "sql", "api", "nlp", "ci/cd", "db"] else s.title()}</span>', unsafe_allow_html=True)
                else:
                    st.write("None")
                    
            with col_extra:
                st.markdown(f"**Additional Candidate Skills ({len(extra_s)})**")
                if extra_s:
                    for s in sorted(list(extra_s))[:10]:  # Cap display at 10 additional skills
                        st.markdown(f'<span class="badge badge-primary">{s.upper() if s in ["aws", "gcp", "sql", "api", "nlp", "ci/cd", "db"] else s.title()}</span>', unsafe_allow_html=True)
                    if len(extra_s) > 10:
                        st.write(f"*... and {len(extra_s)-10} more*")
                else:
                    st.write("None")
                    
        with tab_profile:
            st.markdown("### Profile Details")
            
            col_edu, col_skill_cat = st.columns(2)
            
            with col_edu:
                st.markdown("#### Education History")
                for edu in candidate["Education"]:
                    st.markdown(f"- **{edu}**")
                    
            with col_skill_cat:
                st.markdown("#### Skills Categorization")
                # Parse the raw resume again to show categorized skills
                cat_skills = extract_skills(candidate["RawText"])
                if cat_skills:
                    for cat, sks in cat_skills.items():
                        st.markdown(f"**{cat}**:")
                        sks_str = ", ".join(sks)
                        st.markdown(f"<span style='color: #4F46E5;'>{sks_str}</span>", unsafe_allow_html=True)
                else:
                    st.write("No categorized skills identified.")
                    
        with tab_resume:
            st.markdown("### Raw Resume Text")
            st.text_area("Extracted Plain Text", value=candidate["RawText"], height=400, disabled=True)
            
            # Simple warning if file contains very little text
            if len(candidate["RawText"].strip().split()) < 50:
                st.warning("⚠️ This resume contains very little extracted text. It might be scanned/an image PDF, or parsing failed. The TF-IDF score may not represent the candidate accurately.")
