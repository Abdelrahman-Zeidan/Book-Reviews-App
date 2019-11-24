import os
import requests

from flask import Flask, session, render_template, jsonify, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from flask_login import login_required, current_user, login_user, logout_user, LoginManager

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/index")
def index():
    return render_template("index.html")






@app.route("/signup", methods=["GET", "POST"])
def signup():
    """sign up for account """

    if request.method == "GET":
        return render_template("signup.html")
    

    elif request.method == "POST":

        loginUser = request.form.get("Username")
        loginUser = loginUser.lower()
        loginUser = loginUser.strip(" ")
        loginPass = request.form.get("Password")


        # Make Sure that the username is not exist in the database
        if db.execute("SELECT username FROM users WHERE username = :username", {"username": loginUser}).rowcount == 1:
            message = "Sorry, Username already exist"
            return render_template("signup.html", Signupmessage = message )
        
        elif db.execute("SELECT username, password FROM users WHERE (username = :username AND password = :password)", {"username": loginUser, "password": loginPass}).rowcount == 0:
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
                        {"username": loginUser, "password": loginPass})

            message = "You have successfully Created your account. Please Go to login page"
            db.commit()
            return render_template("signup.html", Signupmessage= message)




    
@app.route("/login", methods=["GET","POST"])
def login():
    """Log in page"""
    
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        global loginUser
        loginUser = request.form.get("Username")
        loginUser = loginUser.lower()
        loginPass = request.form.get("Password")

        global user
        session['user'] = loginUser 
        if 'user' in session:
            user = session['user']
        

        if db.execute("SELECT username, password FROM users WHERE (username = :username AND password = :password)", {"username": loginUser, "password": loginPass}).rowcount == 0:
            message = "Invalid Username or Password"
            return render_template("login.html", Loginmessage = message)
        else:
            db.commit() 
            return redirect('home')





@app.route("/home", methods=["GET", "POST"])
def home():
    
    if request.method == "GET":  
        return render_template("dashboard.html", username=user)
 
    elif request.method =="POST":
        books = []
        message = ""
        searchValue = request.form.get("SearchText")
        data = db.execute("SELECT * FROM books WHERE (isbn LIKE '%"+searchValue+"%') OR (title LIKE '%"+searchValue+"%') OR (author LIKE '%"+searchValue+"%') ")
            
        for book in data:
            books.append(book)
            
            
        if len(books) == 0:
            message = "Nothing found. Try again"
        
        return render_template("dashboard.html", books=books, message = message, username=user)



@app.route("/book/<string:isbn>", methods=["GET", "POST"])
def book(isbn):

    data = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchone()
    MessageCanNotSubmit = ""
    reviews = []

    secondreview = db.execute("SELECT * FROM reviews WHERE username = :username AND isbn = :isbn", {"username": user, "isbn":isbn}).fetchone()

    if request.method == "POST" and secondreview == None:
        review = request.form.get("review")
        rate = request.form.get("rate")
        db.execute("INSERT INTO reviews (isbn, review, rating, username) VALUES (:isbn, :review, :rating, :username)", {"isbn":isbn, "review":review, "rating":rate, "username":user})
        db.commit()


    if request.method == "POST" and secondreview != None:
        MessageCanNotSubmit = "Sorry, only one review is available for each user"

    reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn",{"isbn":isbn}).fetchall()
    BookDetails = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchall()


    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "xlpbBtF35BjRihX8yJNwQ", "isbns": isbn})
    goodreadsData = res.json()

    work_ratings_count = goodreadsData['books'][0]['work_ratings_count']
    average_rating = goodreadsData['books'][0]['average_rating']

    return render_template("book.html", data=data, BookDetails=BookDetails, username=user, reviews=reviews, MessageCanNotSubmit = MessageCanNotSubmit, work_ratings_count=work_ratings_count, average_rating=average_rating )






@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    BookAPI = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchone()
    if BookAPI is None:
        return jsonify({"Error": "Invalid ISBN"}), 422

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "xlpbBtF35BjRihX8yJNwQ", "isbns": isbn})
    goodreadsData = res.json()

    work_ratings_count = goodreadsData['books'][0]['work_ratings_count']
    average_rating = goodreadsData['books'][0]['average_rating']

    return jsonify({
        "title": BookAPI.title ,
        "author": BookAPI.author,
        "year": BookAPI.year,
        "isbn": BookAPI.isbn,
        "review_count": work_ratings_count,
        "average_score": average_rating
        })





@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))