import re
from typing import List, Set, Dict

# Predefined skill vocabulary categorized for granular explanation
SKILL_TAXONOMY = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c\\+\\+", "c#", "ruby", "go", "rust", 
        "php", "html", "css", "sql", "r", "matlab", "scala", "kotlin", "swift", "objective-c", "bash", "shell"
    ],
    "Frameworks & Libraries": [
        "react", "angular", "vue", "django", "flask", "fastapi", "spring boot", "express", 
        "node\\.js", "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy", 
        "spark", "hadoop", "hibernate", "\\.net", "jquery", "bootstrap", "next\\.js", "tailwind"
    ],
    "Databases": [
        "postgresql", "mysql", "mongodb", "sqlite", "oracle", "redis", "cassandra", "dynamodb", "mariadb"
    ],
    "DevOps & Cloud": [
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform", "ansible", 
        "git", "github", "gitlab", "ci/cd", "linux", "nginx", "apache", "circleci"
    ],
    "Methodologies & Domains": [
        "machine learning", "deep learning", "nlp", "natural language processing", "computer vision", 
        "agile", "scrum", "rest api", "graphql", "microservices", "data science", "web development", 
        "software engineering", "oop", "system design", "data structures", "algorithms"
    ],
    "Soft Skills": [
        "communication", "leadership", "teamwork", "problem solving", "critical thinking", 
        "time management", "collaboration", "project management", "mentoring", "adaptability"
    ]
}

def clean_text(text: str) -> str:
    """Helper to lowercase and clean text for uniform matching."""
    if not text:
        return ""
    # Lowercase and normalize spaces
    return " ".join(text.lower().split())

def extract_skills(text: str) -> Dict[str, List[str]]:
    """
    Extracts skills from text based on the taxonomy.
    
    Args:
        text (str): The raw text to extract skills from.
        
    Returns:
        Dict[str, List[str]]: A dictionary mapping categories to lists of matched skills.
    """
    cleaned = clean_text(text)
    extracted = {}
    
    for category, skills in SKILL_TAXONOMY.items():
        matched_in_category = []
        for skill in skills:
            # Match with word boundaries to avoid partial matches (e.g. 'go' in 'google')
            # For skills with special characters like c++, we escape them appropriately
            pattern = rf"\b{skill}\b"
            if re.search(pattern, cleaned):
                # Clean up formatting for user presentation
                display_name = skill.replace("\\", "")
                if display_name == "c++":
                    display_name = "C++"
                elif display_name == "c#":
                    display_name = "C#"
                elif display_name == ".net":
                    display_name = ".NET"
                else:
                    display_name = display_name.title()
                matched_in_category.append(display_name)
        if matched_in_category:
            extracted[category] = sorted(list(set(matched_in_category)))
            
    return extracted

def get_flat_skills(text: str) -> Set[str]:
    """
    Extracts skills and returns a flat set of skill names (lowercased).
    """
    skills_dict = extract_skills(text)
    flat = set()
    for skills in skills_dict.values():
        for s in skills:
            flat.add(s.lower())
    return flat
