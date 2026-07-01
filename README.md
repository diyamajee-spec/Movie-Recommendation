# Age-Based Multilingual Movie Recommendation System

A complete, beginner-friendly yet professional web-based movie recommendation system built with **Python, Flask, HTML, CSS, JavaScript, and Machine Learning**. 

This system recommends movies based on the user's **Age Group**, **Preferred Genre**, and **Preferred Language**, using a hybrid model of **NLP Content-Based Filtering (TF-IDF & Cosine Similarity)** and popularity/rating heuristics. It features a fully responsive, modern **Netflix-inspired Dark UI** with real-time interactive client-side sliders and page transition animations.

---

## Key Features

1. **Safety First (Age Group Filter):** 
   - **Kids (Ages 5–12):** Restricts results strictly to *Animation, Family, Adventure, Fantasy, and Comedy*, while completely blocking action, drama, thriller, horror, crime, and adult-flagged movies.
   - **Teens (Ages 13–17):** Allows general action, drama, and adventure, but filters out horror, thriller, crime, and adult-flagged content.
   - **Adults (Ages 18+):** Provides unrestricted access to the entire movie catalog.
2. **Multilingual Catalog:** Recommends Hollywood and Indian movies across 4 major languages:
   - English (Hollywood)
   - Hindi (Bollywood)
   - Tamil (Kollywood)
   - Telugu (Tollywood)
3. **Hybrid Recommendation Engine:**
   - Pre-filters by language and age-suitability constraints.
   - Applies **TF-IDF Vectorization** on movie overviews to capture plot details.
   - Calculates **Cosine Similarity** to compare plot context against selected genres or target movies.
   - Computes a final weighted hybrid score: 
     $$Score = 50\% \text{ Similarity} + 30\% \text{ Popularity} + 20\% \text{ Rating}$$
4. **Netflix-Inspired Premium Design:** Deep dark theme with crimson highlights, rounded glassmorphic cards, glowing borders, smooth zoom hover animations, and loading screens.
5. **Interactive Client-Side Filters:** Interactive range sliders on the recommendations page filter movies in real-time by *Minimum Rating, Release Year, and Popularity* without refreshing the page.
6. **Dynamic TMDB Poster Fetching (Bonus):** Automatically connects to the TMDB API to retrieve high-resolution posters if a TMDB API key is configured. Otherwise, falls back gracefully to dataset URLs and styled placeholding.

---

## Folder Structure

```text
Movie-Recommendation/
├── app.py                   # Main Flask application (routes, blueprints, logic)
├── recommendation.py        # Recommendation Engine (TF-IDF, Cosine Similarity, Age filter)
├── preprocess.py            # Preprocessing script (reads db, cleans genres/ratings, creates CSV)
├── requirements.txt         # Project package dependencies
├── README.md                # Project documentation
│
├── data/
│   ├── movies.csv           # Cleaned combined movie dataset (generated)
│   ├── tfidf_vectorizer.pkl # Serialized TF-IDF vectorizer (generated)
│   └── tfidf_matrix.pkl     # Serialized TF-IDF matrix (generated)
│
├── static/
│   ├── css/
│   │   └── style.css        # Netflix-inspired stylesheet (dark theme, animations)
│   ├── js/
│   │   └── main.js          # JavaScript for loading states and interactive filters
│   └── images/              # Static media assets
│
└── templates/
    ├── base.html            # Core layout wrapper with navbar & footer
    ├── index.html           # Home page with recommendation wizard & search
    ├── recommend.html       # Movie results page with sidebar sliders & cards
    ├── about.html           # Project details, logic, and architecture docs
    ├── contact.html         # Contact form with user feedback
    └── 404.html             # Custom styled page-not-found page
```

---

## Installation & Setup

Follow these steps to run the project locally on your machine.

### Prerequisites
Make sure you have **Python 3.8+** installed on your system.

### Step 1: Clone or Navigate to the Workspace
Open your terminal in the directory where this project is located:
```bash
cd c:\Users\hp\Movie-Recommendation
```

### Step 2: Initialize Virtual Environment
Create a clean virtual environment `.venv`:
```bash
# Windows
python -m venv .venv

# Mac/Linux
python3 -m venv .venv
```

### Step 3: Activate the Environment
```bash
# Windows (Command Prompt)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Mac/Linux
source .venv/bin/activate
```

### Step 4: Install Dependencies
Install all required libraries using the requirements file:
```bash
pip install -r requirements.txt
```

### Step 5: Run the Dataset Preprocessing Script
Before starting the web server, you must run the pre-processing script to parse the SQLite database, merge the Hindi/Tamil/Telugu movies, clean genres, scale ratings, and fit the TF-IDF models:
```bash
python preprocess.py
```
This generates `movies.csv` and the serialized models inside the `data/` folder.

### Step 6: Configure Optional TMDB API Key (Bonus)
To enable automatic movie poster fetching for movies that don't have posters, create a `.env` file in the project root:
```env
TMDB_API_KEY=your_actual_tmdb_api_key_here
SECRET_KEY=any_random_string_for_flask_sessions
```
*Note: If no API key is specified, the system will use the poster paths already stored in the dataset.*

### Step 7: Launch the Flask Web Application
Start the Flask development server:
```bash
python app.py
```

### Step 8: Visit the Application
Open your browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## Verification & Testing Guide

To verify that the system is functioning correctly:

1. **Verify Home Page Load:** Go to `http://127.0.0.1:5000`. The movie-themed dark hero section and the three recommendation dropdowns (Age Group, Language, Genre) should display cleanly.
2. **Test Age Filtering (Kids Mode):**
   - Select **Kids (Ages 5-12)**, **English (Hollywood)**, and **Animation**.
   - Click "Get Recommendations".
   - You should see kid-friendly movies like *Toy Story*, *Jumanji*, etc.
   - Note that no action, horror, thriller, or adult-themed movies will appear.
3. **Test Multilingual Recommendations:**
   - Select **Adult (18+)**, **Hindi (Bollywood)**, and **Comedy**.
   - You should see Bollywood titles like *3 Idiots*, *Hera Pheri*, *Zindagi Na Milegi Dobara*.
4. **Test Similar Movie Search:**
   - In the search bar at the top, type `Toy Story` or `3 Idiots` and click Search.
   - The app will locate the movie and display 10 other similar movies sorted by their matching score (based on plot similarities and popularity/ratings).
5. **Test Interactive Filters:**
   - On the results page, adjust the sliders for **Min Rating** (e.g. set to 8.0) or **Min Release Year** (e.g. set to 2015).
   - The movie cards should filter in real-time. Cards not meeting the sliders' criteria will fade out.
