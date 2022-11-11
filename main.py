import sqlalchemy
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
import os
import uuid
from flask import Flask, render_template,request,redirect,session
import mysql.connector
import os

app = Flask(__name__)
app.secret_key=os.urandom(24)

conn = mysql.connector.connect(host='localhost',user='root',password='d1i2v3y4',port='3306', database='users')
cursor = conn.cursor()

@app.route('/')
def login():
    return render_template('login.html')


@app.route('/register')
def about():
    return render_template('register.html')


@app.route('/home')
def home():
    if 'user_id' in session:
        return render_template('index.html')
    else:
        return redirect('/')


@app.route('/login_validation' , methods=['POST'])
def local_validation():
    email = request.form.get('email')
    password = request.form.get('password')
    cursor.execute(""" SELECT  * FROM `user` WHERE `email` LIKE '{}' AND `password` LIKE '{}' """ .format(email,password))
    user = cursor.fetchall()
    if len(user)>0:
        session['user_id']=user[0][0]
        return redirect('/musicpage')
    else:
        return redirect('/')


@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form.get('uname')
    email = request.form.get('uemail')
    password = request.form.get('upassword')

    cursor.execute("""  INSERT INTO  `user` (`user_id`,`username`,`email`,`password`)  VALUES  (NULL , '{}','{}','{}') """.format(name,email,password))
    conn.commit()

    cursor.execute(""" SELECT * FROM `user` WHERE `email` LIKE '{}' """ .format(email))
    myuser=cursor.fetchall()
    session['user_id']=myuser[0][0]
    return redirect('/home')


@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect('/')




APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static', 'music')

#app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///music.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300))
    date_created = db.Column(db.DateTime,  default=datetime.now(pytz.timezone('Asia/Kolkata')))

    def __repr__(self):
        return self.title


class Music(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300))
    artist = db.Column(db.String(300))
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))
    filename = db.Column(db.String(300))
    date_created = db.Column(db.DateTime,  default=datetime.now(pytz.timezone('Asia/Kolkata')))

    def __repr__(self):
        return self.title


@app.route('/musicpage', methods=['GET'])
def index():
    albums = Album.query.order_by(Album.date_created).all()
    return render_template('index.html', albums=albums)


@app.route('/Album/Create', methods=['POST', 'GET'])
def album_create():
    if request.method == 'POST':
        album_title = request.form['title']
        new_album = Album(title=album_title)
        try:
            db.session.add(new_album)
            db.session.commit()
            return redirect('/musicpage')
        except:
            return 'Issue in adding the album'
    else:
        return render_template('album-create.html')


@app.route('/Album/Delete/<int:id>', methods=['POST', 'GET'])
def album_delete(id):
    album = Album.query.get_or_404(id)
    if request.method == 'POST':
        try:
            db.session.delete(album)
            db.session.commit()
            return redirect('/musicpage')
        except:
            return 'Issue in deleting the album'
    else:
        return render_template('album-delete.html', album=album)


@app.route('/Album/Update/<int:id>', methods=['POST', 'GET'])
def album_update(id):
    album = Album.query.get_or_404(id)
    if request.method == 'POST':
        album.title = request.form['title']
        try:
            db.session.commit()
            return redirect('/musicpage')
        except:
            return 'Issue in updating the album'
    else:
        return render_template('album-update.html', album=album)


@app.route('/Album/Music/<int:id>', methods=['GET'])
def music_list(id):
    album = Album.query.get_or_404(id)
    musics = Music.query.filter(album.id == Music.album_id).order_by(Music.date_created).all()
    return render_template('music-list.html', musics=musics, album=album)


@app.route('/Album/Music/Create/<int:id>', methods=['POST', 'GET'])
def music_create(id):
    album = Album.query.get_or_404(id)
    if request.method == 'POST':
        music_title = request.form['title']
        music_artist = request.form['artist']
        song = request.files['song']
        if song:
            songUUID = str(uuid.uuid1())
            new_music = Music(title=music_title, artist=music_artist, album_id=album.id, filename=(songUUID+'.mp3'))
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], (songUUID+'.mp3'))
        else:
            new_music = Music(title=music_title, artist=music_artist, album_id=album.id)
        try:
            db.session.add(new_music)
            db.session.commit()
            if song:
                song.save(full_filename)
            return redirect('/Album/Music/'+str(album.id))
        except:
            return 'Issue in adding the music'
    else:
        return render_template('music-create.html', album=album)


@app.route('/Album/Music/Delete/<int:id>', methods=['POST', 'GET'])
def music_delete(id):
    music = Music.query.get_or_404(id)
    album_id = music.album_id
    if request.method == 'POST':
        try:
            if music.filename:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], music.filename))
            db.session.delete(music)
            db.session.commit()
            return redirect('/Album/Music/'+str(album_id))
        except:
            return 'Issue in deleting the music'
    else:
        return render_template('music-delete.html', music=music)


@app.route('/Album/Music/Update/<int:id>', methods=['POST', 'GET'])
def music_update(id):
    music = Music.query.get_or_404(id)
    album_id = music.album_id
    album = Album.query.get_or_404(album_id)
    if request.method == 'POST':
        music.title = request.form['title']
        music.artist = request.form['artist']
        song = request.files['song']
        if song:
            if music.filename:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], music.filename))
            songUUID = str(uuid.uuid1())
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], (songUUID + '.mp3'))
            song.save(full_filename)
            music.filename = songUUID+'.mp3'
        try:
            db.session.commit()
            return redirect('/Album/Music/'+str(album_id))
        except:
            return 'Issue in deleting the music'
    else:
        return render_template('music-update.html', music=music, album=album)


@app.route('/Album/Music/Open/<int:id>', methods=['POST', 'GET'])
def music_open(id):
    music = Music.query.get_or_404(id)
    album_id = music.album_id
    album = Album.query.get_or_404(album_id)
    song = 'music/'+ str(music.filename)
    print(song)
    return render_template('music-open.html', music=music, album=album, song=song)


@app.route('/Search', methods=['POST'])
def search():
    search_str = request.form['search']
    albums = Album.query.filter(Album.title.contains(search_str)).order_by(Album.date_created).all()
    musics = Music.query.filter(Music.title.contains(search_str)).order_by(Music.date_created).all()
    artists = Music.query.filter(Music.artist.contains(search_str)).order_by(Music.date_created).all()
    return render_template('music-search.html', albums=albums, musics=musics, artists=artists, string=search_str)


if __name__ == "__main__":
    app.run(debug=True)
