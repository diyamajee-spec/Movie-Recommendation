import os
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity

# Constants for file paths
CSV_PATH = 'data/movies.csv'
VECTORIZER_PATH = 'data/tfidf_vectorizer.pkl'
MATRIX_PATH = 'data/tfidf_matrix.pkl'

# Global variables to cache dataset in memory
_movies_df = None
_vectorizer = None
_tfidf_matrix = None

# Genre queries for profile-based recommendation
GENRE_QUERIES = {
    "Action": "action packed battle shootout explosion stunt chase fight hero martial arts mission danger suspense hero warrior gunfight combat",
    "Adventure": "adventure journey quest exploration wilderness voyage discovery treasure hunt explorer path trip map survival",
    "Animation": "animation animated cartoon drawings voice over cute characters family kids toys fairy tale pixar disney anime",
    "Comedy": "comedy funny hilarious joke laugh humor fun amusement parody satire sitcom comical amusing laughing",
    "Crime": "crime police detective gangster murder robbery theft mafia suspense dark investigation inspector jail law court case criminal",
    "Drama": "drama emotional relationship life society family struggle tragedy tears conflict feelings characters life story biographical",
    "Fantasy": "fantasy magic mythical creatures wizard spell sword sorcery castle legend folklore magical supernatural elf dragon kingdom",
    "Family": "family kids children heartwarming parents together fun wholesome growing up friendly animated values relatives",
    "History": "history historical true events biography king queen war revolution period drama document archival ancient dynasty",
    "Horror": "horror scary ghost demon monster blood violence fear dark haunted house nightmare terror fright creepy jump scare supernatural",
    "Music": "music musical song dance singer band concert instrument soundtrack melody voice opera rhythm pop rock singing musician",
    "Mystery": "mystery detective clue puzzle unsolved murder secrets hidden case suspicious investigator investigate missing suspect",
    "Romance": "romance love relationship couple romantic husband wife dates emotional kissing heartbreak dates dating sweetheart marry",
    "Science Fiction": "science fiction sci-fi futuristic robot alien space time travel technology outer space spaceship galaxy laser spaceship galaxy",
    "Thriller": "thriller suspense intense chase mystery murderer danger crime tension psychologist twist survival stalker hostage",
    "War": "war soldiers battle army navy airforce military historic fight conflict weapons tragedy combat defense invasion battleground",
    "Western": "western cowboy desert horse sheriff gunfight outlaw saloon wild west frontier ranch saddle gunslinger",
    "Documentary": "documentary real interview research educational facts nature history chronicles biography true life interviewees"
}

def load_data():
    """
    Load dataset and models into global cache
    """
    global _movies_df, _vectorizer, _tfidf_matrix
    
    if _movies_df is not None:
        return _movies_df, _vectorizer, _tfidf_matrix
        
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Cleaned dataset not found at {CSV_PATH}. Please run preprocess.py first.")
        
    _movies_df = pd.read_csv(CSV_PATH)
    # Ensure columns have correct types
    _movies_df["Movie Title"] = _movies_df["Movie Title"].fillna("").astype(str)
    _movies_df["Genres"] = _movies_df["Genres"].fillna("").astype(str)
    _movies_df["Overview"] = _movies_df["Overview"].fillna("").astype(str)
    _movies_df["Language"] = _movies_df["Language"].fillna("").astype(str)
    _movies_df["Release Year"] = _movies_df["Release Year"].fillna(2000).astype(int)
    _movies_df["Vote Average"] = _movies_df["Vote Average"].fillna(5.0).astype(float)
    _movies_df["Popularity"] = _movies_df["Popularity"].fillna(10.0).astype(float)
    _movies_df["Adult Flag"] = _movies_df["Adult Flag"].fillna(0).astype(int)
    _movies_df["Original Language"] = _movies_df["Original Language"].fillna("").astype(str)
    _movies_df["Runtime"] = _movies_df["Runtime"].fillna(120).astype(int)
    _movies_df["Director"] = _movies_df["Director"].fillna("Unknown Director").astype(str)
    _movies_df["Cast"] = _movies_df["Cast"].fillna("Unknown Cast").astype(str)
    _movies_df["Backdrop URL"] = _movies_df["Backdrop URL"].fillna("").astype(str)
    _movies_df["Poster URL"] = _movies_df["Poster URL"].fillna("").astype(str)
    
    if os.path.exists(VECTORIZER_PATH) and os.path.exists(MATRIX_PATH):
        _vectorizer = joblib.load(VECTORIZER_PATH)
        _tfidf_matrix = joblib.load(MATRIX_PATH)
    else:
        print("TF-IDF models not found. Fitting vectorizer dynamically...")
        corpus = []
        for idx, row in _movies_df.iterrows():
            txt = row['Overview']
            if not txt.strip():
                txt = f"{row['Movie Title']}. A movie in the genre of {row['Genres']}."
            corpus.append(txt)
        from sklearn.feature_extraction.text import TfidfVectorizer
        _vectorizer = TfidfVectorizer(stop_words='english', min_df=1, max_df=0.9, ngram_range=(1, 2))
        _tfidf_matrix = _vectorizer.fit_transform(corpus)
        
    return _movies_df, _vectorizer, _tfidf_matrix

def is_movie_suitable(genres_str, adult, age_group):
    """
    Determine if a movie is suitable for a given age group based on genres and adult flag.
    
    Kids:
      Allowed: Animation, Family, Adventure, Fantasy, Comedy
      Excluded: Excludes all other genres and Adult content
    Teen:
      Allowed: Adventure, Comedy, Fantasy, Action, Science Fiction, Drama, Animation, Family
      Excluded: Excludes Horror, Crime, Thriller, War, Western, History, Music, Mystery, Romance, Documentary, and Adult content
    Adult:
      Allowed: Everything
    """
    if adult == 1:
        return False
        
    movie_genres = [g.strip() for g in genres_str.split(',')]
    if not movie_genres:
        return False
        
    if age_group == 'Kids':
        allowed_kids = {'Animation', 'Family', 'Adventure', 'Fantasy', 'Comedy'}
        # All genres in this movie must be in the kids allowed list
        return all(g in allowed_kids for g in movie_genres)
        
    elif age_group == 'Teen':
        allowed_teen = {'Adventure', 'Comedy', 'Fantasy', 'Action', 'Science Fiction', 'Drama', 'Animation', 'Family'}
        # All genres in this movie must be in the teen allowed list
        return all(g in allowed_teen for g in movie_genres)
        
    else:  # Adult
        return True

def get_recommendations_by_preferences(age_group, preferred_genre, preferred_lang):
    """
    Recommend top 10 movies based on Age Group, Preferred Genre, and Preferred Language
    using a Hybrid Content-Filtering & Popularity/Rating system.
    """
    df, vectorizer, tfidf_matrix = load_data()
    
    # Step 1: Filter dataset by Language and Genre
    # Language match (e.g. 'en', 'hi', 'ta', 'te')
    lang_filtered = df[df['Language'] == preferred_lang]
    
    # Genre match (genres string must contain the preferred genre)
    genre_filtered = lang_filtered[lang_filtered['Genres'].apply(lambda x: preferred_genre in [g.strip() for g in x.split(',')])]
    
    if genre_filtered.empty:
        return []
        
    # Suitability filter based on Age Group
    suitable_indices = []
    for idx, row in genre_filtered.iterrows():
        if is_movie_suitable(row['Genres'], row['Adult Flag'], age_group):
            suitable_indices.append(idx)
            
    if not suitable_indices:
        return []
        
    filtered_df = df.loc[suitable_indices].copy()
    
    # Step 2: Use TF-IDF on movie overviews
    # Retrieve pre-computed TF-IDF representation of filtered movies
    # Compute query vector for the selected genre
    query_text = GENRE_QUERIES.get(preferred_genre, preferred_genre)
    query_vec = vectorizer.transform([query_text])
    
    # Step 3: Use Cosine Similarity to rank similar movies
    filtered_tfidf = tfidf_matrix[suitable_indices]
    cos_similarities = cosine_similarity(query_vec, filtered_tfidf).flatten()
    
    # Step 4: Sort recommendations using Popularity, Vote Average, and Cosine Similarity
    # Normalize Popularity and Vote Average to [0, 1] range relative to the entire dataset
    max_pop = df['Popularity'].max()
    min_pop = df['Popularity'].min()
    pop_range = max_pop - min_pop if max_pop != min_pop else 1.0
    
    normalized_pop = (filtered_df['Popularity'] - min_pop) / pop_range
    normalized_rating = filtered_df['Vote Average'] / 10.0
    
    # Combine scores: 0.5 * Similarity + 0.3 * Popularity + 0.2 * Rating
    scores = (0.5 * cos_similarities) + (0.3 * normalized_pop.values) + (0.2 * normalized_rating.values)
    
    filtered_df['Cosine Similarity'] = cos_similarities
    filtered_df['Recommendation Score'] = np.round(scores * 100, 1)  # Scale to 0-100%
    
    # Sort and return top 50
    top_recommendations = filtered_df.sort_values(by='Recommendation Score', ascending=False).head(50)
    top_recommendations = top_recommendations.fillna("")
    
    return top_recommendations.to_dict(orient='records')

def search_movie_by_title(query_title):
    """
    Search for a movie in the dataset by its title (case-insensitive substring match).
    Returns a list of matching movies.
    """
    df, _, _ = load_data()
    query_title = query_title.strip().lower()
    
    if not query_title:
        return []
        
    # Search for substring match
    matches = df[df['Movie Title'].str.lower().str.contains(query_title, na=False)]
    matches = matches.head(5).fillna("")
    return matches.to_dict(orient='records')

def get_similar_movies(movie_title, age_group='Adult'):
    """
    Find top 10 movies similar to a given movie title based on Cosine Similarity
    of their overviews, filtered by age suitability.
    """
    df, vectorizer, tfidf_matrix = load_data()
    
    # Find the target movie in the dataset (exact or best match)
    matches = df[df['Movie Title'].str.lower() == movie_title.lower()]
    if matches.empty:
        # Fallback to substring
        matches = df[df['Movie Title'].str.lower().str.contains(movie_title.lower(), na=False)]
        if matches.empty:
            return []
            
    target_idx = matches.index[0]
    target_movie = df.loc[target_idx]
    
    # Get the target movie TF-IDF vector
    target_vec = tfidf_matrix[target_idx]
    
    # Calculate cosine similarity with all other movies
    cos_similarities = cosine_similarity(target_vec, tfidf_matrix).flatten()
    
    # Filter suitability based on age group and exclude the target movie itself
    suitable_indices = []
    similarities = []
    
    for idx, row in df.iterrows():
        if idx == target_idx:
            continue
        # Check suitability
        if is_movie_suitable(row['Genres'], row['Adult Flag'], age_group):
            suitable_indices.append(idx)
            similarities.append(cos_similarities[idx])
            
    if not suitable_indices:
        return []
        
    filtered_df = df.loc[suitable_indices].copy()
    similarities = np.array(similarities)
    
    # Hybrid ranking score
    max_pop = df['Popularity'].max()
    min_pop = df['Popularity'].min()
    pop_range = max_pop - min_pop if max_pop != min_pop else 1.0
    
    normalized_pop = (filtered_df['Popularity'] - min_pop) / pop_range
    normalized_rating = filtered_df['Vote Average'] / 10.0
    
    scores = (0.5 * similarities) + (0.3 * normalized_pop.values) + (0.2 * normalized_rating.values)
    
    filtered_df['Cosine Similarity'] = similarities
    filtered_df['Recommendation Score'] = np.round(scores * 100, 1)
    
    # Sort and return top 50
    top_similar = filtered_df.sort_values(by='Recommendation Score', ascending=False).head(50)
    top_similar = top_similar.fillna("")
    return top_similar.to_dict(orient='records')
