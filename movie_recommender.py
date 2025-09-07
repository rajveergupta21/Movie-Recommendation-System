from flask import Flask, request, jsonify, render_template
import csv
from datetime import datetime

app = Flask(__name__)

movies = []
with open('final_dataset.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        poster_path = row.get('poster_path', '')
        movies.append({
            "id": int(row['id']),
            "title": row['title'],
            "genre": row.get('genres', ''),
            "original_language": row['original_language'],
            "overview": row['overview'],
            "popularity": float(row['popularity']) if row['popularity'] else 0.0,
            "release_date": row['release_date'],
            "vote_average": float(row['vote_average']) if row['vote_average'] else 0.0,
            "vote_count": int(row['vote_count']) if row['vote_count'] else 0,
            "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image",
            "poster_backdrop_url": f"https://image.tmdb.org/t/p/original{poster_path}" if poster_path else "https://via.placeholder.com/1280x720?text=No+Backdrop"
        })

def get_abbreviation(title):
    # Generate abbreviation by taking the first letter of each word in the title
    return ''.join(word[0] for word in title.split() if word).lower()

# Route to serve the recommendation questionnaire page
@app.route('/recommendation')
def recommendation_page():
    return render_template('recommendation.html')

@app.route('/recommend_movies', methods=['POST'])
def recommend_movies():
    data = request.get_json()
    # New questionnaire structure:
    # mood: 'happy', 'neutral', 'sad'
    # occasion: 'alone', 'free', 'special'
    # genres: array of up to 3
    # age_appropriateness: 'yes' or 'no'
    # timeline: '5', '10', '15', '25', 'any', 'very old'
    mood = data.get('mood', '').strip().lower()
    occasion = data.get('occasion', '').strip().lower()
    genres = data.get('genres', [])
    if isinstance(genres, str):
        genres = [genres]
    genres = [g.strip().lower() for g in genres if g.strip()]
    age_appropriateness = data.get('age_appropriateness', '').strip().lower()
    timeline = data.get('timeline', '').strip().lower()

    # Map mood to keywords
    mood_keywords = {
        'happy': ['comedy', 'family', 'animation', 'musical'],
        'sad': ['drama', 'tragedy'],
        'neutral': [],
    }
    mood_genre_keywords = mood_keywords.get(mood, [])

    # Optional: Map occasion to genres (for scoring)
    occasion_map = {
        'alone': ['drama', 'mystery', 'thriller'],
        'free': ['comedy', 'adventure'],
        'special': ['romance', 'fantasy', 'animation'],
    }
    occasion_genre_keywords = occasion_map.get(occasion, [])

    # Map timeline options to years or special handling
    timeline_map = {
        '5': 5,
        '10': 10,
        '15': 15,
        '25': 25,
        'any': None,
        'very old': 'very_old'
    }

    timeline_value = timeline_map.get(timeline, None)
    current_year = datetime.now().year

    filtered_movies = []
    for m in movies:
        # Age appropriateness: if 'yes', exclude adult/R-rated movies
        if age_appropriateness == 'yes':
            genre_lower = m['genre'].lower()
            overview_lower = m['overview'].lower()
            title_lower = m['title'].lower()
            # refined check for adult content: match whole words
            adult_terms = ['r', 'r-rated', 'nc-17', 'adult']
            found_adult = False
            # Check for exact words in genre
            genre_words = [word.strip() for word in genre_lower.replace(',', ' ').split()]
            if any(term in genre_words for term in adult_terms):
                found_adult = True
            # Check for whole word matches in overview and title
            overview_words = [word.strip(".,:;!?()[]{}\"'") for word in overview_lower.split()]
            title_words = [word.strip(".,:;!?()[]{}\"'") for word in title_lower.split()]
            if any(term in overview_words for term in adult_terms):
                found_adult = True
            if any(term in title_words for term in adult_terms):
                found_adult = True
            # Also check for "r-rated" and "nc-17" as substrings (for overview, which may say "Rated R" or "NC-17")
            if 'r-rated' in overview_lower or 'nc-17' in overview_lower:
                found_adult = True
            if found_adult:
                continue

        # Timeline filter
        rd = m['release_date']
        if not rd:
            continue
        try:
            release_year = int(rd[:4])
        except Exception:
            continue

        if timeline_value == 'very_old':
            # Include only movies released more than 25 years ago from current year
            if release_year > (current_year - 25):
                continue
        elif isinstance(timeline_value, int):
            if release_year < (current_year - timeline_value):
                continue
        elif timeline_value is None:
            # 'any' timeline selected; include all
            pass
        else:
            # If timeline value is unrecognized, exclude movie
            continue

        filtered_movies.append(m)

    scored_movies = []
    for m in filtered_movies:
        score = 0
        genre_lower = m['genre'].lower()
        # +1 per matching selected genre (up to 3 max)
        genre_matches = 0
        for g in genres[:3]:
            if g and g in genre_lower:
                genre_matches += 1
        score += genre_matches
        # +1 if mood matches genre keywords
        if mood_genre_keywords and any(k in genre_lower for k in mood_genre_keywords):
            score += 1
        # +1 if occasion matches mapping
        if occasion_genre_keywords and any(k in genre_lower for k in occasion_genre_keywords):
            score += 1
        if score > 0:
            scored_movies.append((m, score))

    # Sort by score (desc), then vote_count (desc), then vote_average (desc)
    scored_movies_sorted = sorted(
        scored_movies,
        key=lambda x: (x[1], x[0]['vote_count'], x[0]['vote_average']),
        reverse=True
    )
    top_movies = [m[0] for m in scored_movies_sorted[:2]]
    return jsonify(top_movies)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/movies', methods=['GET'])
def get_movies():
    genre = request.args.get('genre')
    if genre:
        genre_lower = genre.lower()
        filtered_movies = [movie for movie in movies if genre_lower in movie['genre'].lower()]
        return jsonify(filtered_movies)
    return jsonify(movies)

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    query = data.get('query', '')
    query_norm = query.strip().lower()
    if not query_norm:
        # Return top 20 movies sorted by vote_count
        top_movies = sorted(movies, key=lambda x: x['vote_count'], reverse=True)[:20]
        return jsonify(top_movies)
    # Search in genre, title, overview, and abbreviation (case-insensitive)
    recommended = [
        movie for movie in movies
        if query_norm in movie['genre'].lower()
        or query_norm in movie['title'].lower()
        or query_norm in movie['overview'].lower()
        or query_norm == get_abbreviation(movie['title'])
    ]
    recommended_sorted = sorted(recommended, key=lambda x: x['vote_count'], reverse=True)[:20]
    return jsonify(recommended_sorted)


# New route to display details for a specific movie
@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    # Find the movie with the given id
    movie = next((m for m in movies if m['id'] == movie_id), None)
    if movie is None:
        return render_template('movie_detail.html', movie=None), 404
    return render_template('movie_detail.html', movie=movie)


# Global error handlers
from flask import make_response

@app.errorhandler(404)
def not_found_error(error):
    # Check if the client accepts JSON (API request)
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({"error": "Not found"}), 404
    # Otherwise, render template
    return render_template('error.html', error_message="Page not found (404)"), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
