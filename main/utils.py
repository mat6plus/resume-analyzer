import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import spacy
import logging

logger = logging.getLogger(__name__)

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def preprocess_text(text):
    # Tokenize the text
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords and non-alphabetic tokens
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token.isalpha() and token not in stop_words]
    
    # Lemmatize the tokens
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    return ' '.join(tokens)

def extract_keywords(text, n=20):
    # Preprocess the text
    processed_text = preprocess_text(text)
    
    # Check if the processed text is empty
    if not processed_text.strip():
        logger.warning("Processed text is empty after preprocessing.")
        return []
    
    # Use spaCy for named entity recognition
    doc = nlp(processed_text)
    entities = [ent.text for ent in doc.ents]
    
    # Use TF-IDF to extract important words
    try:
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([processed_text])
        feature_names = vectorizer.get_feature_names_out()
        
        # Get top N words based on TF-IDF scores
        tfidf_scores = tfidf_matrix.toarray()[0]
        top_n_indices = tfidf_scores.argsort()[-n:][::-1]
        top_n_words = [feature_names[i] for i in top_n_indices]
        
        # Combine named entities and top TF-IDF words
        keywords = list(set(entities + top_n_words))
        
        return keywords[:n]  # Return top N unique keywords
    except ValueError as e:
        logger.error(f"Error in TF-IDF vectorization: {str(e)}")
        return entities[:n] if entities else []  # Fall back to named entities or empty list

def calculate_match_percentage(job_description, resume_text):
    # Preprocess both texts
    processed_job = preprocess_text(job_description)
    processed_resume = preprocess_text(resume_text)
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([processed_job, processed_resume])
    
    # Calculate cosine similarity
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    
    # Convert similarity to percentage
    match_percentage = cosine_sim[0][0] * 100
    
    return round(match_percentage, 2)

def generate_suggestions(job_description, resume_text):
    try:
        job_keywords = set(extract_keywords(job_description))
        resume_keywords = set(extract_keywords(resume_text))
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        job_keywords = set()
        resume_keywords = set()

    suggestions = []

    if job_keywords and resume_keywords:
        missing_keywords = job_keywords - resume_keywords
        if missing_keywords:
            suggestions.append(f"Consider adding the following keywords to your resume: {', '.join(missing_keywords)}")
    else:
        suggestions.append("Unable to extract keywords. Please ensure your resume and the job description contain relevant content.")

    if len(resume_keywords) < 10:
        suggestions.append("Your resume might benefit from more detailed information about your skills and experiences.")

    # Check for common sections
    common_sections = ['education', 'experience', 'skills', 'projects']
    missing_sections = [section for section in common_sections if section.lower() not in resume_text.lower()]
    if missing_sections:
        suggestions.append(f"Consider adding the following sections to your resume: {', '.join(missing_sections)}")

    if not suggestions:
        suggestions.append("No specific suggestions at this time. Your resume appears to be well-aligned with the job description.")

    return suggestions

def extract_text_from_resume(file):
    # Implementation depends on the file type (pdf, docx, etc.)
    # For simplicity, let's assume it's a text file
    return file.read().decode('utf-8')