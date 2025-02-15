import streamlit as st
import pickle
import pandas as pd
import requests

def main():
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False

    if not st.session_state.is_authenticated:
        login()
    else:
        recommendation_system_page()

def login():
    st.title("Giriş Sayfası")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    login_button = st.button("Giriş Yap")

    if login_button:
        # Kullanıcı kimlik doğrulaması işlemi
        if username == "admin" and password == "admin":
            st.session_state.is_authenticated = True
            st.experimental_rerun()  # Sayfayı tekrar yükleyerek öneri sistemi sayfasına yönlendir
        else:
            st.error("Hatalı kullanıcı adı veya şifre. Lütfen tekrar deneyin.")

def recommendation_system_page():
    st.title("Film Öneri Sistemi")
 
    def fetch_poster(movie_id):
        response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key=a13b6212f7ee597d68db363f59528425&language=en-US'.format(movie_id))
        data = response.json()
        return "https://image.tmdb.org/t/p/w500/" + data['poster_path']

    def recommend(movie):
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key= lambda x:x[1])[1:6]

        recommended_movies = []
        recommended_movies_posters = []
        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            # fetch poster from API
            recommended_movies.append(movies.iloc[i[0]].title)
            recommended_movies_posters.append(fetch_poster(movie_id))
        return recommended_movies,recommended_movies_posters

    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)

    similarity = pickle.load(open('similarity.pkl', 'rb'))

    selected_movie_name = st.selectbox(
        'Hangi filmi aramak istersiniz?',
        movies['title'].values
    )

    if st.button('Öner'):
        names,posters = recommend(selected_movie_name)
   
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.text(names[0])
            st.image(posters[0])
        with col2:
            st.text(names[1])
            st.image(posters[1])
        with col3:
            st.text(names[2])
            st.image(posters[2])
        with col4:
            st.text(names[3])
            st.image(posters[3])
        with col5:
            st.text(names[4])
            st.image(posters[4])

if __name__ == "__main__":
    main()
