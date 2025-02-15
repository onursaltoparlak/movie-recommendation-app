import streamlit as st
import mysql.connector
import hashlib
import requests
import pickle
import pandas as pd
from PIL import Image

# MySQL bağlantısı için gerekli bilgiler
db_host = 'localhost'
db_user = 'root'
db_password = ''
db_name = 'kullanicilar'


# MySQL bağlantısını oluşturma fonksiyonu
def create_connection():
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"MySQL veritabanına bağlanırken hata: {e}")
        return None

# Kullanıcının şifresini sıfırlama fonksiyonu
def reset_password(kadi, yeni_sifre):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        hashed_password = hashlib.sha256(yeni_sifre.encode()).hexdigest()
        cursor.execute("UPDATE kullanici SET sifre = %s WHERE kadi = %s", (hashed_password, kadi))
        conn.commit()
        st.success("Şifre başarıyla sıfırlandı!")
    except mysql.connector.Error as e:
        st.error(f"Hata: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def reset_password_page():
    st.title("Şifre Sıfırlama")

    kadi = st.text_input("Kullanıcı Adı", key="kadi_input")
    yeni_sifre = st.text_input("Yeni Şifre", type="password", key="yeni_pwd")
    yeni_sifre_onay = st.text_input("Yeni Şifreyi Tekrar Girin", type="password", key="yeni_onay")

    reset_button = st.button("Şifreyi Sıfırla")

    if reset_button:
        if yeni_sifre == yeni_sifre_onay:
            reset_password(kadi, yeni_sifre)
        else:
            st.error("Yeni şifreler uyuşmuyor. Lütfen tekrar deneyin.")


# Kullanıcıyı veritabanına kaydetme fonksiyonu
def register_user(kadi, email, sifre):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        hashed_password = hashlib.sha256(sifre.encode()).hexdigest()
        cursor.execute("INSERT INTO kullanici (kadi, email, sifre) VALUES (%s, %s, %s)", (kadi, email, hashed_password))
        conn.commit()
        st.success("Kullanıcı başarıyla kaydedildi!")
    except mysql.connector.Error as e:
        st.error(f"Hata: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Kullanıcı girişi işlemi
def login():
    st.title("Kullanıcı Girişi")
    kadi = st.text_input("Kullanıcı Adı", key="username_input")
    sifre = st.text_input("Şifre", type="password", key="user_pwd")
    login_button = st.button("Giriş Yap")

    if login_button:
        # Kullanıcı kimlik doğrulaması işlemi
        conn = create_connection()
        cursor = conn.cursor()
        hashed_password = hashlib.sha256(sifre.encode()).hexdigest()
        cursor.execute("SELECT * FROM kullanici WHERE kadi = %s AND sifre = %s", (kadi, hashed_password))
        user = cursor.fetchone()

        if user:
            st.session_state.is_authenticated = True
            st.experimental_rerun()  # Sayfayı tekrar yükleyerek öneri sistemi sayfasına yönlendir
        else:
            st.error("Hatalı kullanıcı adı veya şifre. Lütfen tekrar deneyin.")

# Kullanıcı kayıt işlemi
def register():
    st.title("Yeni Kullanıcı Kaydı")
    new_username = st.text_input("Kullanıcı Adı")
    new_email = st.text_input("E-posta Adresi")
    new_password = st.text_input("Şifre", type="password")
    confirm_password = st.text_input("Şifreyi Onayla", type="password")
    register_button = st.button("Kayıt Ol")

    if register_button:
        if new_password == confirm_password:
            register_user(new_username, new_email, new_password)
        else:
            st.error("Şifreler uyuşmuyor. Lütfen tekrar deneyin.")


def degerlendirme(kadi, puan):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO degerlendirme (kadi, puan) VALUES (%s, %s)", (kadi, puan))
        conn.commit()
        st.success("Değerlendirdiğiniz için teşekkürler!")
    except mysql.connector.Error as e:
        st.error(f"Hata: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def recommendation_system_page():
    st.markdown("<h1 style='text-align: center; color: red; font-size: 60px'>MovieFlix'i Kullanmaya Hemen Başlayın!</h1>", unsafe_allow_html=True)

    def fetch_poster(movie_id):
        response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key=a13b6212f7ee597d68db363f59528425&language=en-US'.format(movie_id))
        data = response.json()
        return "https://image.tmdb.org/t/p/w500/" + data['poster_path']

    def recommend(movie):
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

        recommended_movies = []
        recommended_movies_posters = []
        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            # fetch poster from API
            recommended_movies.append(movies.iloc[i[0]].title)
            recommended_movies_posters.append(fetch_poster(movie_id))
        return recommended_movies, recommended_movies_posters

    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)

    similarity = pickle.load(open('similarity.pkl', 'rb'))

    selected_movie_name = st.selectbox(
        'Hangi filmi aramak istersiniz?',
        movies['title'].values
    )

    with st.form(key='degerlendirme_form'):
        names, posters = recommend(selected_movie_name)
        st.write("Değerlendirme:")
    
        # Input alanı ve puanlama mesajı
        kadi = st.text_input("Kullanıcı Adı", key="username_input")
        puan = st.number_input("Puanınızı Girin", min_value=1, max_value=5)
    
        # Değerlendirme butonu
        evaluate_button_clicked = st.form_submit_button("Değerlendir")
    
        # Kullanıcının değer girmesi ve değerlendirme butonuna tıklaması durumunda teşekkür mesajı gösterilecek
        if evaluate_button_clicked:
            try:
                conn = create_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO degerlendirme (kadi, puan) VALUES (%s, %s)", (kadi, puan))
                conn.commit()
                st.success("Değerlendirdiğiniz için teşekkürler!")
            except mysql.connector.Error as e:
                st.error(f"Hata: {e}")
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()

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

def main():
    st.sidebar.title("Ana Sayfa")  # Sol taraftaki sidebar başlığı eklendi
    img = Image.open('logo_2.png')
    
    left_co, cent_co,last_co = st.columns(3)
    with cent_co:
        st.image(img, width=250)

    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False

    if not st.session_state.is_authenticated:
        st.markdown("<h1 style='text-align: center; color: red; font-size: 60px;'>MovieFlix'e Hoş Geldiniz!</h1>", unsafe_allow_html=True)  # Ana sayfa başlığı eklendi
        page = st.sidebar.radio("Giriş Yap veya Kaydol", ["Kullanıcı Girişi", "Yeni Kullanıcı Kaydı", "Şifre Sıfırlama"])

        if page == "Kullanıcı Girişi":
            login()
        elif page == "Yeni Kullanıcı Kaydı":
            register()
        elif page == "Şifre Sıfırlama":
            reset_password_page()
    else:
        recommendation_system_page()

if __name__ == "__main__":
    main()