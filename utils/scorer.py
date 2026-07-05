from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, Any, Set
from utils.skill_extractor import get_flat_skills, extract_skills

def calculate_similarity_score(jd_text: str, resume_text: str) -> float:
    """
    Computes TF-IDF and Cosine Similarity score between JD and resume.
    
    Args:
        jd_text (str): Raw text of the job description.
        resume_text (str): Raw text of the resume.
        
    Returns:
        float: Similarity percentage (0 to 100).
    """
    if not jd_text.strip() or not resume_text.strip():
        return 0.0
        
    try:
        # Initialize TF-IDF Vectorizer
        # We use English stop words and lowercase matching
        vectorizer = TfidfVectorizer(stop_words='english')
        
        # Fit and transform the texts
        tfidf_matrix = vectorizer.fit_transform([jd_text, resume_text])
        
        # Compute Cosine Similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        
        # Scale to 0-100 and round to 2 decimal places
        score = float(similarity[0][0]) * 100
        return round(score, 2)
    except Exception:
        # Fallback if TF-IDF calculation fails (e.g., lack of vocabulary)
        return 0.0

def generate_explanation(jd_text: str, resume_text: str, score: float) -> str:
    """
    Generates a natural-language explanation of why a candidate received their score,
    highlighting matched skills, missing skills, and overall compatibility.
    
    Args:
        jd_text (str): Job description text.
        resume_text (str): Resume text.
        score (float): Cosine similarity score.
        
    Returns:
        str: A detailed textual explanation.
    """
    jd_skills = get_flat_skills(jd_text)
    resume_skills = get_flat_skills(resume_text)
    
    # If the JD contains no identifiable skills, compare resume to overall technical terms
    if not jd_skills:
        if resume_skills:
            skills_sample = ", ".join(list(resume_skills)[:5])
            return f"Job description has generic requirements. Candidate possesses skills in: {skills_sample} (TF-IDF Match: {score}%)."
        return f"Evaluated based on textual match with a score of {score}%."
        
    matched = resume_skills.intersection(jd_skills)
    missing = jd_skills - resume_skills
    
    # Clean up names for presentation
    matched_names = []
    # Match the case of the skill from the taxonomy if possible
    # We can retrieve display names by parsing again and flat listing or title casing
    for skill in matched:
        matched_names.append(skill.upper() if skill in ["aws", "gcp", "sql", "api", "nlp", "ci/cd", "db"] else skill.title())
        
    missing_names = []
    for skill in missing:
        missing_names.append(skill.upper() if skill in ["aws", "gcp", "sql", "api", "nlp", "ci/cd", "db"] else skill.title())
        
    matched_count = len(matched)
    total_count = len(jd_skills)
    
    explanation_parts = []
    
    # Core skill match sentence
    if matched_count > 0:
        sample_matched = ", ".join(matched_names[:4])
        if len(matched_names) > 4:
            sample_matched += ", etc."
        explanation_parts.append(
            f"Matched {matched_count} out of {total_count} required skills ({round(matched_count/total_count * 100)}% skill overlap), "
            f"including {sample_matched}."
        )
    else:
        explanation_parts.append(f"Matched 0 out of {total_count} required skills.")
        
    # Mention critical gaps if any
    if missing_names and matched_count < total_count:
        sample_missing = ", ".join(missing_names[:3])
        explanation_parts.append(f"Missing skills from job description: {sample_missing}.")
        
    # Summary of text relevance
    if score >= 60:
        explanation_parts.append("Candidate text matches the job description profile very closely.")
    elif score >= 40:
        explanation_parts.append("Candidate has moderate text relevance and matches some job description requirements.")
    else:
        explanation_parts.append("Low text relevance. The candidate's background does not align closely with this JD.")
        
    return " ".join(explanation_parts)
