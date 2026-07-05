import re
import os
import datetime
from typing import List

def extract_name(text: str, file_name: str = "") -> str:
    """
    Extracts the candidate's name from the resume text using heuristics.
    If it fails, falls back to cleaning up the file name.
    
    Args:
        text (str): Raw resume text.
        file_name (str, optional): The name of the file being parsed.
        
    Returns:
        str: The extracted name.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return _clean_filename(file_name) if file_name else "Unknown Candidate"
        
    ignored_keywords = {"resume", "curriculum", "vitae", "cv", "summary", "contact", "profile", "about", "objective"}
    
    # Analyze the first 8 lines
    for line in lines[:8]:
        # Filter out lines that look like emails, URLs, or locations
        if "@" in line or "http" in line or "www" in line or "|" in line or ".com" in line:
            continue
            
        # Ignore lines with too many numbers (like phone numbers)
        digits = sum(c.isdigit() for c in line)
        if digits > 3:
            continue
            
        words = line.split()
        if not words or len(words) < 2 or len(words) > 4:
            continue
            
        # Ensure name words start with a capitalized letter
        if all(w[0].isupper() for w in words if w.isalpha()):
            # Verify it's not a section header in all-caps
            if line.upper() == line and line.lower() in ignored_keywords:
                continue
            return line
            
    # Fallback to file name if provided
    if file_name:
        return _clean_filename(file_name)
        
    return "Unknown Candidate"

def _clean_filename(file_name: str) -> str:
    """Cleans up a filename to serve as a candidate name."""
    name = os.path.splitext(os.path.basename(file_name))[0]
    # Replace underscores/dashes with spaces
    name = re.sub(r'[-_]', ' ', name)
    # Remove common resume search terms
    name = re.sub(r'(?i)\b(?:resume|cv|screening|profile|parsed|file|v\d+)\b', '', name).strip()
    # Capitalize each word
    name = " ".join([w.capitalize() for w in name.split() if w])
    return name if name else "Unknown Candidate"

def extract_education(text: str) -> List[str]:
    """
    Extracts education details from the resume text.
    
    Args:
        text (str): Raw resume text.
        
    Returns:
        List[str]: List of extracted education records.
    """
    education_lines = []
    lines = text.split("\n")
    
    degree_indicators = [
        "bachelor", "master", "ph.d", "phd", "doctorate",
        "b.s.", "m.s.", "b.tech", "m.tech", "b.e.", "m.e.", "bca", "mca", "mba", "b.sc", "m.sc",
        "university", "college", "institute of technology"
    ]
    
    for line in lines:
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in degree_indicators):
            cleaned = line.strip()
            # Clean up bullet points
            cleaned = re.sub(r'^[•\-\*]\s*', '', cleaned)
            # Remove double spaces
            cleaned = re.sub(r'\s+', ' ', cleaned)
            # Limit length to filter out long paragraphs that happen to contain a keyword
            if 10 < len(cleaned) < 120 and cleaned not in education_lines:
                education_lines.append(cleaned)
                
    if not education_lines:
        return ["Education details not explicitly found"]
        
    return education_lines[:3]  # Return top 3 entries

def extract_experience(text: str) -> float:
    """
    Extracts total years of experience from resume text.
    First checks for direct statements of experience, then calculates from year ranges.
    
    Args:
        text (str): Raw resume text.
        
    Returns:
        float: Years of experience.
    """
    # 1. Search for direct experience statements
    exp_patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years? of experience|years? experience|yrs? exp|yrs? of exp|years? in|years? of professional experience)",
        r"(?:experience|work history)[:\-\s]+(\d+(?:\.\d+)?)\s*years?"
    ]
    
    for pattern in exp_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                # Return the maximum declared experience
                scores = [float(m) for m in matches]
                if max(scores) > 0:
                    return max(scores)
            except ValueError:
                continue
                
    # 2. Fallback: Parse year ranges (e.g. "2018 - 2021", "2020 - Present") and merge them
    year_range_pattern = r"\b(19\d{2}|20\d{2})\s*(?:-|–|—|to)\s*(19\d{2}|20\d{2}|present|current|now)\b"
    matches = re.findall(year_range_pattern, text, re.IGNORECASE)
    
    current_year = datetime.datetime.now().year
    ranges = []
    
    for start, end in matches:
        try:
            start_yr = int(start)
            if end.lower() in ["present", "current", "now"]:
                end_yr = current_year
            else:
                end_yr = int(end)
            
            if 1970 < start_yr <= end_yr <= current_year:
                ranges.append((start_yr, end_yr))
        except ValueError:
            continue
            
    if not ranges:
        return 0.0
        
    # Sort and merge overlapping year ranges to avoid double-counting
    ranges.sort(key=lambda x: x[0])
    merged = []
    for r in ranges:
        if not merged:
            merged.append(r)
        else:
            prev_start, prev_end = merged[-1]
            curr_start, curr_end = r
            if curr_start <= prev_end:
                merged[-1] = (prev_start, max(prev_end, curr_end))
            else:
                merged.append(r)
                
    total_exp = sum(end - start for start, end in merged)
    return float(total_exp)
