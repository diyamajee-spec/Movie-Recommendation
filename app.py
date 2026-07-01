import os
from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, jsonify
import requests
from dotenv import load_dotenv

# Import recommendation functions
from recommendation import (
    load_data,
    get_recommendations_by_preferences,
    search_movie_by_title,
    get_similar_movies
)

# Load environment variables
load_dotenv()
TMDB_API_KEY = os.getenv('TMDB_API_KEY')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_cine_rec_2026')

# -----------------------------------------------------------------------------
# Poster Fetching Helper (Bonus TMDB API Integration)
# -----------------------------------------------------------------------------
def fetch_poster_url(title, release_year=None):
    """
    Query the TMDB Search API or fallback to OMDb API to find a movie poster dynamically.
    Returns the poster URL or None.
    """
    # 1. Try TMDB if API key is present
    if TMDB_API_KEY:
        try:
            url = "https://api.themoviedb.org/3/search/movie"
            params = {
                "api_key": TMDB_API_KEY,
                "query": title
            }
            if release_year:
                params["primary_release_year"] = int(release_year)
                
            response = requests.get(url, params=params, timeout=3)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    poster_path = results[0].get("poster_path")
                    if poster_path:
                        return f"https://image.tmdb.org/t/p/w500{poster_path}"
        except Exception as e:
            print(f"TMDB Poster Fetch Error: {e}")

    # 2. Fallback: Query OMDb API (using free public key 'thewdb')
    try:
        url = "http://www.omdbapi.com/"
        params = {
            "t": title.strip(),
            "apikey": "thewdb"
        }
        if release_year:
            params["y"] = int(release_year)
            
        response = requests.get(url, params=params, timeout=3)
        if response.status_code == 200:
            data = response.json()
            poster = data.get("Poster")
            if poster and poster != "N/A" and poster.startswith("http"):
                return poster
    except Exception as e:
        print(f"OMDb Poster Fetch Error: {e}")
        
    return None

def fill_missing_posters(movies_list):
    """
    Fill in missing poster URLs in a list of movies by calling TMDB/OMDb.
    Caches fetched results in the global memory DataFrame.
    """
    for movie in movies_list:
        poster = movie.get('Poster URL', '')
        if not poster or poster == "" or str(poster).lower() in ["nan", "none"]:
            dyn_poster = fetch_poster_url(movie['Movie Title'], movie['Release Year'])
            if dyn_poster:
                movie['Poster URL'] = dyn_poster
                # Cache in global DataFrame so subsequent lookups don't call the API again
                try:
                    df, _, _ = load_data()
                    mask = df['Movie Title'] == movie['Movie Title']
                    if mask.any():
                        df.loc[mask, 'Poster URL'] = dyn_poster
                except Exception as e:
                    print(f"Error caching poster in dataframe: {e}")
    return movies_list

# -----------------------------------------------------------------------------
# Blueprints Definition
# -----------------------------------------------------------------------------
main_bp = Blueprint('main', __name__)
recommender_bp = Blueprint('recommender', __name__)

# --- MAIN BLUEPRINT ROUTES ---

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # In a real app, save to db or send email here.
        # We will flash a message and redirect to contact page.
        flash(f"Thank you, {name}! Your message has been sent successfully. We will get back to you soon.", "success")
        return redirect(url_for('main.contact'))
        
    return render_template('contact.html')

# --- RECOMMENDER BLUEPRINT ROUTES ---

@recommender_bp.route('/recommend', methods=['POST'])
def recommend():
    age_group = request.form.get('age_group')
    preferred_genre = request.form.get('genre')
    preferred_lang = request.form.get('language')
    
    if not age_group or not preferred_genre or not preferred_lang:
        flash("Please complete all form fields to get recommendations.", "error")
        return redirect(url_for('main.index'))
        
    # Map language codes to names for UI display
    lang_map = {
        "en": "English (Hollywood)",
        "hi": "Hindi (Bollywood)",
        "ta": "Tamil (Kollywood)",
        "te": "Telugu (Tollywood)"
    }
    language_name = lang_map.get(preferred_lang, preferred_lang)
    
    # Get recommendations
    try:
        recs = get_recommendations_by_preferences(age_group, preferred_genre, preferred_lang)
        # Dynamically fetch posters from TMDB API if local poster is missing (Bonus)
        recs = fill_missing_posters(recs)
    except Exception as e:
        flash(f"An error occurred while generating recommendations: {str(e)}", "error")
        return redirect(url_for('main.index'))
        
    return render_template(
        'recommend.html',
        movies=recs,
        age_group=age_group,
        language_name=language_name,
        preferred_genre=preferred_genre,
        search_movie=None
    )

@recommender_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    age_group = request.args.get('age_group', 'Adult')  # Default to Adult if searching directly
    
    if not query or not query.strip():
        flash("Please enter a movie title to search.", "error")
        return redirect(url_for('main.index'))
        
    # Search for movie in local database
    matches = search_movie_by_title(query)
    
    if not matches:
        flash(f"No movie found matching '{query}'. Try searching for 'Toy Story', '3 Idiots', or 'RRR'.", "warning")
        return redirect(url_for('main.index'))
        
    # Take the first matched movie
    target_movie = matches[0]
    
    # Dynamically fetch target movie poster if missing
    if not target_movie.get('Poster URL') or target_movie['Poster URL'] == "":
        dyn_poster = fetch_poster_url(target_movie['Movie Title'], target_movie['Release Year'])
        if dyn_poster:
            target_movie['Poster URL'] = dyn_poster
            
    # Get similar movies
    try:
        similar_recs = get_similar_movies(target_movie['Movie Title'], age_group)
        # Fetch posters for similar movies
        similar_recs = fill_missing_posters(similar_recs)
    except Exception as e:
        flash(f"An error occurred while fetching similar movies: {str(e)}", "error")
        return redirect(url_for('main.index'))
        
    return render_template(
        'recommend.html',
        movies=similar_recs,
        age_group=age_group,
        search_movie=target_movie
    )

@recommender_bp.route('/api/poster', methods=['GET'])
def api_poster():
    title = request.args.get('title', '').strip()
    year = request.args.get('year', '').strip()
    if not title:
        return jsonify({"poster": ""})
        
    try:
        url = "http://www.omdbapi.com/"
        params = {
            "t": title,
            "apikey": "thewdb"
        }
        if year and year.isdigit() and int(year) > 1900:
            params["y"] = int(year)
            
        response = requests.get(url, params=params, timeout=3)
        if response.status_code == 200:
            data = response.json()
            poster = data.get("Poster")
            if poster and poster != "N/A" and poster.startswith("http"):
                # Cache it in global DataFrame
                try:
                    df, _, _ = load_data()
                    mask = df['Movie Title'] == title
                    if mask.any():
                        df.loc[mask, 'Poster URL'] = poster
                except Exception as e:
                    print(f"Error caching poster in dataframe: {e}")
                return jsonify({"poster": poster})
    except Exception as e:
        print(f"API poster search error: {e}")
    return jsonify({"poster": ""})

@recommender_bp.route('/api/search', methods=['GET'])
def api_search():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify([])
        
    try:
        matches = search_movie_by_title(query)
        # Process and fetch missing posters for autocomplete
        matches = fill_missing_posters(matches)
        results = []
        for movie in matches:
            results.append({
                "title": movie['Movie Title'],
                "year": movie['Release Year'],
                "poster": movie['Poster URL'],
                "rating": movie['Vote Average'],
                "genres": movie['Genres'],
                "language": movie.get('Language', 'en'),
                "backdrop": movie.get('Backdrop URL', ''),
                "overview": movie.get('Overview', ''),
                "director": movie.get('Director', 'Unknown Director'),
                "cast": movie.get('Cast', 'Unknown Cast'),
                "runtime": movie.get('Runtime', 120),
                "popularity": movie.get('Popularity', 10.0)
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recommender_bp.route('/api/similar', methods=['GET'])
def api_similar():
    title = request.args.get('title', '').strip()
    age_group = request.args.get('age_group', 'Adult').strip()
    if not title:
        return jsonify([])
        
    try:
        recs = get_similar_movies(title, age_group)
        recs = fill_missing_posters(recs)
        results = []
        for movie in recs:
            results.append({
                "title": movie['Movie Title'],
                "year": movie['Release Year'],
                "poster": movie['Poster URL'],
                "rating": movie['Vote Average'],
                "genres": movie['Genres'],
                "language": movie.get('Language', 'en'),
                "backdrop": movie.get('Backdrop URL', ''),
                "overview": movie.get('Overview', ''),
                "director": movie.get('Director', 'Unknown Director'),
                "cast": movie.get('Cast', 'Unknown Cast'),
                "runtime": movie.get('Runtime', 120),
                "popularity": movie.get('Popularity', 10.0)
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------------------------
# Blueprint Registration & Error Handlers
# -----------------------------------------------------------------------------
app.register_blueprint(main_bp)
app.register_blueprint(recommender_bp)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(FileNotFoundError)
def file_not_found_handler(e):
    if "movies.csv" in str(e) or "movies.db" in str(e):
        return render_template('db_missing.html'), 500
    return render_template('500.html'), 500

# Pre-load dataset cache into memory on startup
with app.app_context():
    try:
        load_data()
        print("Dataset and TF-IDF models successfully loaded in memory.")
    except Exception as e:
        print(f"Warning: Failed to load dataset on startup. Error: {e}")

if __name__ == '__main__':
    # Run the web server
    app.run(host='127.0.0.1', port=5000, debug=True)
