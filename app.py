from flask import Flask, request, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['RESULT_FOLDER'] = 'results/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limita o tamanho do upload a 16MB

# Garante que os diretórios existam
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

def extract_usernames_from_html(soup):
    usernames = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith("https://www.instagram.com/"):
            username = href.replace("https://www.instagram.com/", "").rstrip("/")
            if username:
                usernames.append(username)
    return usernames

def process_files(followers_file, following_file, option):
    followers_html = BeautifulSoup(followers_file, 'html.parser')
    following_html = BeautifulSoup(following_file, 'html.parser')

    followers = set(extract_usernames_from_html(followers_html))
    following = set(extract_usernames_from_html(following_html))

    if option == 'sigo_e_nao_me_segue':
        result = following - followers
    elif option == 'nao_sigo_e_me_segue':
        result = followers - following
    else:  # sigo_e_me_segue
        result = followers & following

    result_file_path = os.path.join(app.config['RESULT_FOLDER'], f'result_{option}.txt')
    with open(result_file_path, 'w', encoding='utf-8') as file:
        for user in result:
            file.write(user + '\n')
    
    return result_file_path

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        followers_file = request.files['followers_file']
        following_file = request.files['following_file']
        option = request.form['option']

        followers_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(followers_file.filename))
        following_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(following_file.filename))

        followers_file.save(followers_path)
        following_file.save(following_path)

        with open(followers_path, 'r', encoding='utf-8') as f_followers, open(following_path, 'r', encoding='utf-8') as f_following:
            result_file_path = process_files(f_followers.read(), f_following.read(), option)

        os.remove(followers_path)
        os.remove(following_path)

        return send_from_directory(app.config['RESULT_FOLDER'], os.path.basename(result_file_path), as_attachment=True)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
