import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# Home (index) page
@app.route("/")
@app.route("/index")
def index():
    reviews = mongo.db.reviews.find({})
    return render_template('index.html', reviews=reviews)

# Reviews Page
@app.route("/get_reviews")
def reviews():
    reviews = mongo.db.reviews.find()
    return render_template("reviews.html", reviews=reviews)


# Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check database to see if username already exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # Put new user into session cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful")
        return redirect(url_for(
            "create_review", username=session["user"])) 
    return render_template("register.html")


@app.route("/create_review", methods=["GET", "POST"])
def create_review():
    if request.method == "POST":
        # Assuming 'current_user_id' is available in the session or another method to identify the current user
        current_user_id = session.get("user_id")
        
        review_data = {
            "movie_title": request.form.get("movie_title"),
            "genre": request.form.get("genre"),
            "subtitle": request.form.get("subtitle"),
            "review": request.form.get("review"),
            "username": session["user"]
        }
        # Insert the review into the reviews collection
        mongo.db.reviews.insert_one(review_data)
        
        flash("Review Successfully Added")
        return redirect(url_for("reviews"))
        
    genres = mongo.db.genres.find()  # Assuming 'genres' is the collection name
    return render_template("create_review.html", genres=genres)


# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # check hashed password matches users password input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Hi {}!".format(
                        request.form.get("username")))
                    return redirect(url_for(
                        "create_review", username=session["user"]))
            else:
                # Password doesn't match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # Username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)