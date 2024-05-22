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
    reviewshome = mongo.db.reviews.find({}).limit(3)
    return render_template('index.html', reviews=reviewshome)

# Reviews Page
@app.route("/get_reviews")
def reviews():
    if 'user' not in session or not session['user']:
        return redirect(url_for('unauthorised'))
    reviews = mongo.db.reviews.find() 
    return render_template("reviews.html", reviews=reviews)

# Search on reviews page
@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    reviews = mongo.db.reviews.find({"$text": {"$search": query}}) 
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
            "reviews", username=session["user"])) 
    return render_template("register.html")

# create review
@app.route("/create_review", methods=["GET", "POST"])
def create_review():
    if 'user' not in session or not session['user']:
        return redirect(url_for('unauthorised'))
    if request.method == "POST":
        # Assuming 'current_user_id' is available in the session or another method to identify the current user
        current_user_id = session.get("user_id")
        
        review_data = {
            "movie_title": request.form.get("movie_title"),
            "genre": request.form.get("genre"),
            "subtitle": request.form.get("subtitle"),
            "review": request.form.get("review"),
            "rating": request.form.get("rating"),
            "username": session["user"]
        }
        # Insert the review into the reviews collection
        mongo.db.reviews.insert_one(review_data)
        
        flash("Review Successfully Added")
        return redirect(url_for("reviews"))
        
    categories = mongo.db.categories.find().sort("genre_name", 1)
    return render_template("create_review.html", categories=categories)

#edit review
@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    if 'user' not in session or not session['user']:
        return redirect(url_for('unauthorised'))
    if request.method == "POST":
        submit = {
            "movie_title": request.form.get("movie_title"),
                "genre": request.form.get("genre"),
                "subtitle": request.form.get("subtitle"),
                "review": request.form.get("review"),
                "rating": request.form.get("rating"),
                "username": session["user"]
        }
        mongo.db.reviews.update_one({"_id": ObjectId(review_id)}, {"$set": submit})
        flash("Review Successfully Updated")
        return redirect(url_for('reviews'))

    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    categories = mongo.db.categories.find().sort("genre_name", 1)
    ratings = mongo.db.ratings.find().sort("rating_number", 1)
    return render_template("edit_review.html", review=review, categories=categories, ratings=ratings)

# Delete Review
@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    mongo.db.reviews.remove({"_id": ObjectId(review_id)})
    flash("Review Successfully Deleted")
    return redirect(url_for('reviews'))

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
                        "reviews", username=session["user"]))
            else:
                # Password doesn't match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # Username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))
            
    return render_template("login.html")

# logout button
@app.route("/logout")
def logout():
    if 'user' not in session or not session['user']:
        return redirect(url_for('unauthorised'))
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


#unauthorised access for users that aren't logged in or have no account
@app.route("/unauthorised")
def unauthorised():
    return render_template("unauthorised.html")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)