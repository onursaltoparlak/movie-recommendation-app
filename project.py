import base64
import streamlit as st
import mysql.connector
import hashlib
import pickle
import pandas as pd
import requests
import random
from PIL import Image


def set_background(png_file):
    with open(png_file, "rb") as f:
        bin_str = base64.b64encode(f.read()).decode()
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)


set_background("C:/Users/Onursal Toparlak/Desktop/Tüm Dosyalar/Taslaklar/movie_recommendation/netflix.jpg")


db_host = 'localhost'
db_user = 'root'
db_password = ''
db_name = 'movie'



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


def reset_password(user_name, old_password, new_password):
    try:
        conn = create_connection()
        if not conn:  # Eğer bağlantı başarısız olursa hata ver
            st.error("Veritabanı bağlantısı kurulamadı!")
            return

        cursor = conn.cursor()

        # Eski şifrenin doğruluğunu kontrol et
        hashed_old_password = hashlib.sha256(old_password.encode()).hexdigest()
        cursor.execute("SELECT * FROM users WHERE user_name = %s AND password = %s", (user_name, hashed_old_password))
        user = cursor.fetchone()

        if user:
            # Yeni şifreyi hashle
            hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()
            # "password" alanını güncelle
            cursor.execute("UPDATE users SET password = %s WHERE user_name = %s", (hashed_new_password, user_name))
            conn.commit()
            st.markdown("<div style='text-align:center; padding: 10px; background-color: darkgreen; color: darkgray; border: 2px solid red; border-radius: 10px;'><h1>Şifreniz başarıyla sıfırlandı!</h1></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align:center; padding: 10px; background-color: red; color: darkgray; border: 2px solid red; border-radius: 10px;'><h1>Eski şifrenizi yanlış girdiniz!</h1></div>", unsafe_allow_html=True)

    except mysql.connector.Error as e:
        st.error(f"Hata: {e}")

    finally:
        # cursor değişkeni tanımlı mı kontrol et
        if 'cursor' in locals() and cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def reset_password_page():
    st.markdown("<div style='text-align:center; padding: 10px; background-color: black; border: 2px solid red; border-radius: 10px;'><h1 style='color: white;'>Şifre Sıfırlama</h1></div>", unsafe_allow_html=True)
    st.write("")

    st.markdown("<div style='text-align:left; padding: 10px; background-color: black; border: 2px solid red; border-radius: 10px;'><h3 style='color: white;'>Kullanıcı Adı</h3></div>", unsafe_allow_html=True)
    user_name = st.text_input("", key="kadi_input")

    st.markdown("<div style='text-align:left; padding: 10px; background-color: black; border: 2px solid red; border-radius: 10px;'><h3 style='color: white;'>Eski Şifre</h3></div>", unsafe_allow_html=True)
    old_pwd_input = st.text_input("", type="password", key="eski_pwd")

    st.markdown("<div style='text-align:left; padding: 10px; background-color: black; border: 2px solid red; border-radius: 10px;'><h3 style='color: white;'>Yeni Şifre</h3></div>", unsafe_allow_html=True)
    password = st.text_input("", type="password", key="yeni_pwd")

    st.markdown("<div style='text-align:left; padding: 10px; background-color: black; border: 2px solid red; border-radius: 10px;'><h3 style='color: white;'>Yeni Şifreyi Tekrar Girin</h3></div>", unsafe_allow_html=True)
    pwd_verification = st.text_input("", type="password", key="yeni_onay")

    reset_button = st.button("Şifreyi Sıfırla")

    if reset_button:
        if password == pwd_verification:
            reset_password(user_name, old_pwd_input, password)
        else:
            st.markdown("<div style='text-align:center; padding: 10px; background-color: red; color: darkgray; border: 2px solid red; border-radius: 10px;'><h1>Yeni şifreler uyuşmuyor. Lütfen tekrar deneyiniz!</h1></div>", unsafe_allow_html=True)


# Auth::user()
# Auth::user()->id
# id, username, email, password
# değerlendirme tablondaki kullanıcı adı mert olan mesela onun users tablosundaki id sini değerlendirme tablosundan bulup alıcaksın

# Kullanıcıyı veritabanına kaydetme fonksiyonu
def register_user(username, email, password):
    try:
        conn = create_connection()
        if conn is None:
            return
        cursor = conn.cursor()

        # Yeni kullanıcıyı veritabanına ekle
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("INSERT INTO users (user_name, email, password, old_pwd) VALUES (%s, %s, %s, %s)", (username, email, hashed_password, hashed_password))
        conn.commit()
        st.markdown("<div style='text-align:center; padding: 10px; background-color: darkgreen; color: darkgray; border: 2px solid red; border-radius: 10px;'><h1>Kullanıcı Başarıyla Kaydedildi!</h1></div>", unsafe_allow_html=True)

    except mysql.connector.Error as e:
        st.error(f"Hata: {e}")
    finally:
        if conn.is_connected():  # conn'in varlığını ve bağlantının açık olup olmadığını kontrol et
            cursor.close()
            conn.close()

# Kullanıcı girişi işlemi
def login():
    st.markdown("<div style='text-align:center; padding: 10px; background-color: black; border: 1px solid #ff0000; border-radius: 10px;'><h1 style='color: white;'>Kullanıcı Girişi</h1></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown("<div style='text-align:left; padding: 10px; background-color: black; border: 1px solid #ff0000; border-radius: 10px;'><h3 style='color: white;'>Kullanıcı Adı</h3></div>", unsafe_allow_html=True)
    user_name = st.text_input("", key="username_input")

    st.markdown("<div style='text-align:left; padding: 10px; background-color: black; border: 1px solid #ff0000; border-radius: 10px;'><h3 style='color: white;'>Şifre</h3></div>", unsafe_allow_html=True)
    password = st.text_input("", type="password", key="user_pwd")
    login_button = st.button("Giriş Yap")

    if login_button:
        try:
            conn = create_connection()
            if conn is None:  # Bağlantı başarısızsa çık ve kullanıcıya mesaj ver
                st.error("Veritabanına bağlanılamadı.")
                return

            cursor = conn.cursor()

            # Kullanıcı adı için veritabanından bilgileri getir
            cursor.execute("SELECT * FROM users WHERE user_name = %s", (user_name,))
            user = cursor.fetchone()

            if user:
                user_dict = dict(zip([desc[0] for desc in cursor.description], user))
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                if hashed_password == user_dict["password"]:
                    st.markdown("<div style='text-align:center; padding: 10px; background-color: darkgreen; color: darkgray; border: 2px solid red; border-radius: 10px;'><h1>Başarıyla Giriş Yaptınız!</h1></div>", unsafe_allow_html=True)
                    st.session_state.is_authenticated = True
                    st.session_state.user_name = user_name
                    st.experimental_rerun()
                else:
                    st.markdown("<div style='text-align:center; padding: 10px; background-color: red; color: darkgray; border: 2px solid red; border-radius: 10px;'><h1>Hatalı şifre! Lütfen tekrar deneyiniz!</h1></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align:center; padding: 10px; background-color: red; color: darkgray; border: 2px solid red; border-radius: 10px;'><h1>Hatalı kullanıcı adı! Lütfen tekrar deneyiniz!</h1></div>", unsafe_allow_html=True)

        except mysql.connector.Error as e:
            st.error(f"Hata: {e}")
        finally:
            if conn.is_connected():  # conn'in varlığını ve bağlantının açık olup olmadığını kontrol et
                cursor.close()
                conn.close()


# Kullanıcı kayıt işlemi
def register():
    st.markdown("<div style='text-align:center; padding: 10px; background-color: black; border: 2px solid red; border-radius: 10px;'><h1 style='color: white;'>Yeni Kullanıcı Kaydı</h1></div>", unsafe_allow_html=True)
    st.write("")

    st.markdown("<div style='text-align:left; padding: 10px; background-color: black; border: 2px solid red; border-radius: 10px;'><h3 style='color: white;'>Kullanıcı Adı</h3></div>", unsafe_allow_html=True)
    new_username = st.text_input("", key="new_username")

    st.markdown("<div style='text-align:left; padding: 10px; background-color: black; border: 2px solid red; border-radius: 10px;'><h3 style='color: white;'>E-posta Adresi</h3></div>", unsafe_allow_html=True)
    new_email = st.text_input("", key="new_email")

    st.markdown("<div style='text-align:left; padding: 10px; background-color: black; border: 2px solid red; border-radius: 10px;'><h3 style='color: white;'>Şifre</h3></div>", unsafe_allow_html=True)
    new_password = st.text_input("", type="password", key="new_password")

    st.markdown("<div style='text-align:left; padding: 10px; background-color: black; border: 2px solid red; border-radius: 10px;'><h3 style='color: white;'>Şifreyi Onayla</h3></div>", unsafe_allow_html=True)
    confirm_password = st.text_input("", type="password", key="confirm_password")
    register_button = st.button("Kayıt Ol")

    if register_button:
        if new_password == confirm_password:
            register_user(new_username, new_email, new_password)
        else:
            st.markdown("<div style='text-align:center; padding: 10px; background-color: darkgreen; color: darkgray; border: 2px solid red; border-radius: 10px;'><h1>Şifreler uyuşmuyor. Lütfen tekrar deneyiniz!</h1></div>", unsafe_allow_html=True)




movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))


def give_rating(rating):
    user_name = st.session_state.get("user_name")
    if user_name:
        # Kullanıcı adına göre user_id değerini veritabanından al
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE user_name = %s", (user_name,))
        user_id = cursor.fetchone()
        if user_id:
            user_id = user_id[0]  # id değerini al
            # Derecelendirmeyi "rating" tablosuna eklemek için
            try:
                cursor.execute("INSERT INTO rating (user_id, rating) VALUES (%s, %s)", (user_id, rating))
                conn.commit()
            except mysql.connector.Error as e:
                st.error(f"Hata: {e}")
        else:
            st.markdown("<div style='text-align:center; padding: 10px; background-color: darkgreen; color: darkgray; border: 2px solid red; border-radius: 10px;'><h1>Kullanıcı bulunamadı!</h1></div>", unsafe_allow_html=True)

    else:
        st.error("Kullanıcı giriş yapmadı.")


def fetch_poster(movie_id):
        response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key=a13b6212f7ee597d68db363f59528425&language=en-US'.format(movie_id))
        data = response.json()
        return "https://image.tmdb.org/t/p/w500/" + data['poster_path']


# Önerilecek film sayısı
suggested_movies_count = 8

# CSV dosyasından film türlerini yükleme
filtered_movie_genres = pd.read_csv("filtered_movie_genres.csv")

# Kullanıcıya sorulacak duygular ve ilgili türler
emotions_to_genres = {
    "Mutlu": ["Comedy", "Animation", "Romance", "Family"],
    "Üzgün": ["Romance", "Music", "Drama", "Documentary"],
    "Heyecanlı": ["Action", "Adventure", "Crime", "Science Fiction"],
    "Öfkeli": ["Action", "Crime", "War", "Thriller"],
    "Korkmuş": ["Horror", "Mystery", "Thriller", "Western"],
    "Meraklı": ["Mystery", "Science Fiction", "Documentary", "History"],
    "Duygusal": ["Romance", "Drama", "Action", "Comedy"],
}

def get_suggested_movies(emotion):
    if emotion in emotions_to_genres:
        relevant_genres = emotions_to_genres[emotion]
        relevant_movies = filtered_movie_genres[filtered_movie_genres["genres"].isin(relevant_genres)]
        suggested_movies = random.sample(list(relevant_movies["title"]), min(len(relevant_movies), suggested_movies_count))
        return suggested_movies
    else:
        return []

def recommendation_system_page():
    st.markdown("""
    <div style='text-align:center; padding: 40px; background-color: white; border: 2px solid red; border-radius: 10px; max-width: 800px; max-height: 300px; margin: 0 auto;'>
        <h1 style='color: red; font-size: 50px; text-align: center;'>MovieFlix'i Kullanmaya Hemen Başlayın!</h1>
    </div>
""", unsafe_allow_html=True)
    
    set_background("C:/Users/Onursal Toparlak/Desktop/Tüm Dosyalar/Taslaklar/movie_recommendation/netflix-fotor-2024042313533.jpg")

    def get_suggested_movies_with_posters(emotion):
        suggested_movies = get_suggested_movies(emotion)
        suggested_movies_with_posters = []
        for movie in suggested_movies:
            poster_url = fetch_poster_new(movie)
            suggested_movies_with_posters.append({"title": movie, "poster": poster_url})
        return suggested_movies_with_posters

    def fetch_poster_new(movie_name):
        # API'ye film ismini göndererek poster URL'sini al
        response = requests.get('https://api.themoviedb.org/3/search/movie', params={'api_key': 'a13b6212f7ee597d68db363f59528425', 'query': movie_name})
        data = response.json()
        if data['results'] and data['results'][0]['poster_path']:
            # İlk sonuçtan poster URL'sini döndür
            return "https://image.tmdb.org/t/p/w500/" + data['results'][0]['poster_path']
        else:
            # Eğer sonuç bulunamazsa veya poster_path yoksa, placeholder bir URL döndür
            return "https://via.placeholder.com/500x750"

    # Kullanıcıya duygu seçimini sağlayan selectbox
    st.write("<div style='text-align:left'><h1>Nasıl Hissediyorsun?</h1></div>", unsafe_allow_html=True)
    selected_emotion = st.selectbox("", options=["Mutlu", "Üzgün", "Heyecanlı", "Öfkeli", "Korkmuş", "Meraklı", "Duygusal"])


    # Geçerli duygu için öneri filmleri al
    suggested_movies = get_suggested_movies_with_posters(selected_emotion)

    if suggested_movies:
        st.write(f"<div style='text-align:left'><h2>İşte size {selected_emotion} hissi için önerilen {suggested_movies_count} film:</h2></div>", unsafe_allow_html=True)
        st.write("")
    
        num_movies = min(len(suggested_movies), suggested_movies_count)  # En fazla belirlenen sayıda film gösterilecek
    
        # Her satırda 4 film gösterilecek şekilde iki sütun oluşturalım
        columns = st.columns(4)
    
        # Filmleri sırayla sütunlara ekleyelim
        for i in range(num_movies):
            movie = suggested_movies[i]
            with columns[i % 4]:
                st.markdown(f'<p style="font-size: 16px; font-weight: bold;">{movie["title"]}</p>', unsafe_allow_html=True)
                st.image(movie["poster"], width=150)
            st.write("")  # Resimler arasında biraz boşluk bırakmak içi buradaki önerilen filmlerin isimlerinin fontunu kalınlaştırabilir misin?

    # filtered_movie_genres isimli csv dosyasını yükle
    filtered_movie_genres = pd.read_csv('filtered_movie_genres.csv')

    # Tüm türleri al
    all_genres = filtered_movie_genres['genres'].unique()

    # Kullanıcıya tür seçme seçeneklerini sun
    st.write("<div style='text-align:left'><h1>Hangi türde film izlemek istersiniz?</h1></div>", unsafe_allow_html=True)
    selected_genre = st.selectbox("", all_genres)

    # Seçilen türe göre filmleri filtrele
    filtered_movies = filtered_movie_genres[filtered_movie_genres['genres'] == selected_genre]

    # Eğer seçilen türde film bulunamazsa kullanıcıya bilgi ver
    if filtered_movies.empty:
        st.warning(f"{selected_genre} türünde film bulunamadı.")
    else:
        # Seçilen türe göre 5 adet rastgele film seç
        recommended_movies = filtered_movies.sample(n=min(5, len(filtered_movies)))['title'].tolist()

    # HTML ve CSS kullanarak film isimleri ve resimleri tek satırda göster
    html_code = '<div style="display:flex;justify-content:center;align-items:center;">'
    for i, movie in enumerate(recommended_movies):
        if i == 2:  # İlk satırın sonunda
            html_code += '</div><div style="display:flex;justify-content:center;align-items:center;">'
        html_code += f'<div style="text-align:center;margin:0 20px;"><h4 style="margin-bottom:5px;">{movie}</h4><img src="{fetch_poster_new(movie)}" style="width:150px;height:225px;"></div>'
    html_code += '</div>'
    
    st.markdown(html_code, unsafe_allow_html=True)

    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")

   
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



    st.write("<div style='text-align:left'><h1>Hangi filmi aramak istersiniz?</h1></div>", unsafe_allow_html=True)
    selected_movie_name = st.selectbox('', movies['title'].values)

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


    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")

    with st.form(key='degerlendirme_form'):
        names, posters = recommend(selected_movie_name)
        st.write("<div style='text-align:center'><h1>Film Önerilerinin Genel Değerlendirmesi</h1></div>", unsafe_allow_html=True)

        # Input alanı ve puanlama mesajı
        st.write("<div style='text-align:left'><h2>Puanınızı Girin:</h2></div>", unsafe_allow_html=True)
        rating = st.number_input("", min_value=1, max_value=5)
    
        # Değerlendirme butonu
        evaluate_button_clicked = st.form_submit_button("Değerlendir")
    
        # Kullanıcının değer girmesi ve değerlendirme butonuna tıklaması durumunda teşekkür mesajı gösterilecek
        if evaluate_button_clicked:
            give_rating(rating)
            st.markdown("<div style='text-align:center; padding: 10px; background-color: darkgreen; color: darkgray; border: 2px solid red; border-radius: 10px;'><h1>Değerlendirmeniz başarıyla kaydedildi. Teşekkür ederiz!</h1></div>", unsafe_allow_html=True)



def main():
    st.sidebar.title("Ana Sayfa")  # Sol taraftaki sidebar başlığı eklendi
    img = Image.open('logo_2.png')

  
    left_co, cent_co,last_co = st.columns(3)
    with cent_co:
        st.image(img, width=250)

    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False

    if not st.session_state.is_authenticated:
      # Ana sayfa başlığı eklendi
        page = st.sidebar.radio("Kullanıcı İşlemleri", ["Kullanıcı Girişi", "Kaydol", "Şifre Sıfırlama"])

        if page == "Kullanıcı Girişi":
            st.markdown("""
            <div style='text-align:center; padding: 20px; background-color: white; border: 2px solid red; border-radius: 10px;'>
            <h1 style='color: red; font-size: 60px;'>MovieFlix'e Hoş Geldiniz!</h1>
            </div>
            """, unsafe_allow_html=True)
            st.write("") 
            login()
        elif page == "Kaydol":
            register()
        elif page == "Şifre Sıfırlama":
            reset_password_page()
    else:
        # Hoş geldiniz mesajını görüntüle
        username = st.session_state.user_name
        capitalized_username = username.capitalize()  # Kullanıcı adının ilk harfini büyük yap
        st.markdown(f"<h1 style='text-align: center; color: white; font-size: 60px; font-weight: bolder;'>{capitalized_username}, Hoş Geldin!</h1>", unsafe_allow_html=True)

        recommendation_system_page()

if __name__ == "__main__":
    main()
