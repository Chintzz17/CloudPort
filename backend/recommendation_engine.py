import pandas as pd
import numpy as np
import re
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
import nltk

# Download NLTK data (only once)
nltk.download('stopwords')
nltk.download('punkt')

class RecommendationEngine:
    def __init__(self, data_path='C:\\Users\\chint\\OneDrive\\Desktop\\Canada Jobs\\CloudPort\\edutech-recommendation-engine\\backend\\data\\Dataset.csv'):
        """Initialize models and load data."""
        self.df, self.vectorizer, self.sbert_model, self.tfidf_matrix, self.embeddings, self.levels = self._load_data_and_models(data_path)

    def _preprocess_text(self, text):
        """Clean and tokenize text."""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        tokens = word_tokenize(text)
        tokens = [word for word in tokens if word not in stopwords.words('english')]
        return ' '.join(tokens)

    def _load_data_and_models(self, data_path):
        """Load data and initialize models."""
        try:
            df = pd.read_csv(data_path)
            df_copy = df.copy()
            df['Title'] = df['Title'].apply(self._preprocess_text)

            # Initialize models
            vectorizer = TfidfVectorizer(ngram_range=(1, 3), stop_words='english')
            sbert_model = SentenceTransformer("all-MiniLM-L6-v2")

            # Generate embeddings
            corpus = df['Title'].tolist()
            X = vectorizer.fit_transform(corpus)
            embeddings = sbert_model.encode(corpus, convert_to_tensor=True)

            return df_copy, vectorizer, sbert_model, X, embeddings, df['Level'].tolist()
        except Exception as e:
            raise RuntimeError(f"Failed to load data/models: {str(e)}")

    def recommend_courses(self, user_input, top_n=10, tfidf_weight=0.2, sbert_weight=0.7, level_weight=0.1):
        """Generate course recommendations."""
        if not all(key in user_input for key in ['course', 'level']):
            raise ValueError("Input must contain 'course' and 'level' keys.")

        try:
            # Vectorize input
            input_vec = self.vectorizer.transform([user_input['course']])
            query_embedding = self.sbert_model.encode(user_input['course'], convert_to_tensor=True)

            # Calculate similarities
            tfidf_sim = cosine_similarity(input_vec, self.tfidf_matrix).flatten()
            sbert_sim = util.cos_sim(query_embedding, self.embeddings).cpu().numpy().flatten()
            level_match = np.array([1 if level == user_input['level'] else 0 for level in self.levels])

            # Combine scores
            final_scores = (
                tfidf_weight * tfidf_sim +
                sbert_weight * sbert_sim +
                level_weight * level_match
            )

            # Get top courses
            top_indices = np.argsort(final_scores)[::-1][:top_n]
            return [{
                'title': self.df['Title'].iloc[i],
                'level': self.df['Level'].iloc[i],
                'score': float(final_scores[i]),
                'link': self.df.get('URL', {}).iloc[i] or '#'
            } for i in top_indices]

        except Exception as e:
            raise RuntimeError(f"Recommendation failed: {str(e)}")