from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie-database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)

db = SQLAlchemy(app)

MOVIE_DB_API_KEY = os.getenv("MOVIE_DB_API_TOKEN")
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    new_rating = StringField(label="Your rating out of 10", validators=[DataRequired()])
    new_review = StringField(label="Your review", validators=[DataRequired()])
    submit = SubmitField(label="Update")


class AddMovieForm(FlaskForm):
    title = StringField(label="Title name", validators=[DataRequired()])
    submit = SubmitField(label="Add movie")


@app.route("/")
def home():
    all_movies = db.session.query(Movie).order_by(Movie.rating)
    movies_count = len(db.session.query(Movie).all())
    for i in range(movies_count):
        all_movies[i].ranking = movies_count-i
    return render_template("index.html", movies=all_movies)


@app.route("/edit/<int:id>", methods=["POST", "GET"])
def edit(id:int):
    movie = Movie.query.filter_by(id=id).first()
    rate_movie_form = RateMovieForm()
    if rate_movie_form.validate_on_submit():
        movie.rating = float(rate_movie_form.new_rating.data)
        movie.review = rate_movie_form.new_review.data
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return render_template("edit.html", movie=movie, form=rate_movie_form)


@app.route("/delete/<int:id>")
def delete(id:int):
    movie = Movie.query.filter_by(id=id).first()
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["POST", "GET"])
def add():
    addMovieForm = AddMovieForm()
    if addMovieForm.validate_on_submit():
        movie_title = addMovieForm.title.data
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "query": movie_title
        }
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {MOVIE_DB_API_KEY}"
        }
        response = requests.get(url, params=params, headers=headers).json()
        movies = response["results"]
        return render_template("select.html", movies=movies)
    else:
        return render_template("add.html", form=addMovieForm)

@app.route("/add_to_db/<int:id>")
def add_to_db(id:int):
    url = f"https://api.themoviedb.org/3/movie/{id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {MOVIE_DB_API_KEY}"
    }
    response = requests.get(url, headers=headers).json()
    new_movie = Movie(
        title=response["title"],
        year=int(response["release_date"][:4]),
        description=response["overview"],
        rating=float(response["vote_average"]),
        img_url=f"https://image.tmdb.org/t/p/w500{response['poster_path']}"
    )
    with app.app_context():
        db.session.add(new_movie)
        db.session.commit()
    return redirect(url_for('edit', id=len(db.session.query(Movie).all())))


if __name__ == '__main__':
    app.run(debug=True)
