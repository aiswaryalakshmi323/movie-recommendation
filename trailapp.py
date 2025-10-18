import pickle
import streamlit as st
import pandas as pd
import requests

TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8"

try:
    movies_dict = pickle.load(open("movie_list.pkl", "rb"))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open("similarity.pkl", "rb"))
except FileNotFoundError:
    st.error("The 'movie_list.pkl' and 'similarity.pkl' files were not found.")
    st.info("Please run the final data processing notebook to generate them.")
    st.stop()



st.set_page_config(page_title="MojFlix", layout="wide")

netflix_theme_css = """
<style>
/* Import a font similar to Netflix's font */
@import url('https://fonts.googleapis.com/css2?family=Helvetica+Neue:wght@400;700&display=swap');

/* Main background */
[data-testid="stAppViewContainer"] {
    background-color: #141414; /* Netflix's dark background color */
    font-family: 'Helvetica Neue', sans-serif;
}

/* Main title styling */
h1 {
    color: #E50914; /* Netflix Red */
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
}

/* Sub-header styling (e.g., "Because you watched...") */
h3 {
    color: #FFFFFF;
    font-weight: 700;
}

/* Button styling */
.stButton>button {
    background-color: #E50914; /* Netflix Red */
    color: #FFFFFF;
    border: none;
    border-radius: 5px;
    font-weight: bold;
    padding: 10px 24px;
    transition: all 0.2s;
}
.stButton>button:hover {
    background-color: #F40612; /* A brighter red on hover */
    transform: scale(1.05);
}

/* Movie Poster Image Styling */
.stImage img {
    border-radius: 8px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.stImage img:hover {
    transform: scale(1.05); /* Slightly enlarge poster on hover */
    box-shadow: 0 0 25px rgba(229, 9, 20, 0.7); /* Red glow effect */
}

/* Movie Caption Styling */
.st-emotion-cache-1l02z68 p {
    color: #FAFAFA;
    font-weight: bold;
    text-align: center;
}
</style>
"""
st.markdown(netflix_theme_css, unsafe_allow_html=True)
st.title("MojFlix")

# --- Helper Functions ---
@st.cache_data
def fetch_hollywood_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
        response = requests.get(url)
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
    except Exception:
        return None
    return None


def get_poster_url(row):

    url = None
    if row.get('origin') == 'Bollywood':
        url = row.get('poster_url')
    else:  # For Hollywood
        url = fetch_hollywood_poster(row.get('movie_id'))

    if not url or pd.isna(url):
        title = row.get('title', 'Movie')
        return f"https://via.placeholder.com/500x750.png?text={title.replace(' ', '+')}"
    return url



def recommend(movie_name, language="All"):
    try:
        movie_index = movies[movies['title'] == movie_name].index[0]
    except IndexError:
        return []

    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies_data = []
    for i in movies_list:
        row = movies.iloc[i[0]]
        if language.lower() != 'all' and row.get('origin', '').lower() != language.lower():
            continue
        recommended_movies_data.append(row)

    return recommended_movies_data


tab1, tab2 = st.tabs(["Recommend by Movie", " Browse by Genre"])

def display_movie_details(movie_row):

    with st.expander("More Info"):

        overview_data = movie_row.get('overview')
        overview_text = ' '.join(overview_data) if isinstance(overview_data, list) else "No description available."
        st.write(f"**Description:** {overview_text}")


        cast_list = movie_row.get('cast')
        if cast_list and isinstance(cast_list, list):
            cast_display = ", ".join([name.title() for name in cast_list])
            st.write(f"**Cast:** {cast_display}")


        crew_list = movie_row.get('crew')
        if crew_list and isinstance(crew_list, list):
            director_display = ", ".join([name.title() for name in crew_list])
            st.write(f"**Director:** {director_display}")



with tab1:
    language_choice_rec = st.selectbox("Filter by:", ["All", "Hollywood", "Bollywood"], key="rec_lang")
    selected_movie_name = st.selectbox("Type or select a movie to get recommendations:", movies['title'].values,
                                       key="rec_movie")

    if st.button("Recommend"):
        with st.spinner('Finding similar movies...'):
            recommendations = recommend(selected_movie_name, language=language_choice_rec)

        if recommendations:
            st.markdown(f" **{selected_movie_name}**")
            cols = st.columns(5)
            for i, movie_row in enumerate(recommendations):
                with cols[i]:
                    st.image(get_poster_url(movie_row), use_container_width=True)
                    st.caption(f"**{movie_row.get('title', '')}** ({movie_row.get('origin', '')})")
                    display_movie_details(movie_row)  # Use the safe display function
        else:
            st.write("No recommendations found.")

with tab2:
    genre_list = ["Action", "Adventure", "Comedy", "Drama", "Romance", "Thriller", "Crime", "Family"]
    language_choice_genre = st.selectbox("Filter by:", ["All", "Hollywood", "Bollywood"], key="genre_lang")
    selected_genre = st.selectbox("Select a genre to browse:", genre_list, key="genre_select")

    if st.button("Show Movies"):
        with st.spinner(f'Finding {selected_genre} movies...'):
            genre_movies = movies[movies['tags'].str.contains(selected_genre.lower().replace(" ", ""), na=False)]
            if language_choice_genre.lower() != 'all':
                genre_movies = genre_movies[genre_movies['origin'].str.lower() == language_choice_genre.lower()]

        if not genre_movies.empty:
            st.markdown(f"### Top {selected_genre} Movies ({language_choice_genre})")
            num_movies = min(len(genre_movies), 10)
            cols_per_row = 5
            for i in range(0, num_movies, cols_per_row):
                cols = st.columns(cols_per_row)
                batch = genre_movies.iloc[i:i + cols_per_row]
                for j, (idx, movie_row) in enumerate(batch.iterrows()):
                    with cols[j]:
                        st.image(get_poster_url(movie_row), use_container_width=True)
                        st.caption(f"**{movie_row.get('title', '')}** ({movie_row.get('origin', '')})")
                        display_movie_details(movie_row)  # Use the safe display function
        else:
            st.write(f"No {selected_genre} movies found.")
