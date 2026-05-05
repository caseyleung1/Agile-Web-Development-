'''creates route for register and login'''

from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.main.models import User
from app import db
from sqlalchemy.exc import IntegrityError

auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Update data from form
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        terms = request.form.get("terms") # Will be 'on' if checked

        # Validating before send form to a server
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template("register.html")

        if not terms:
            flash("You must agree to the Terms and Conditions.", "error")
            return render_template("register.html")

        # 3. Create and Save User
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully! Please sign in.", "success")
            return redirect(url_for("auth.login"))
        
        except IntegrityError:
            db.session.rollback()
            flash("Email or Username already exists. Try another one.", "error")
            
    return render_template("register.html")

@auth.route("/terms")
def terms():
    return render_template("terms.html")

@auth.route("/login", methods=["GET", "POST"])
def login():
    # login logic routing, including send user to register page when not found
    return render_template("login.html")
