from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bgdata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


##CREATE TABLE
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

class Boardgame(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer)
    name = db.Column(db.String(1000))
    img = db.Column(db.String(1000))

db.create_all()


@app.route('/')
def home():
    # Every render_template has a logged_in variable set.
    return render_template("index.html", logged_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if User.query.filter_by(email=request.form.get('email')).first():
            #User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("collection"))

    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
    
        user = User.query.filter_by(email=email).first()
        #Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('collection'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/collection')
@login_required
def collection():
    users_boardgames = Boardgame.query.filter_by(owner=current_user.id).all()
    return render_template("collection.html", name=current_user.name, boardgames=users_boardgames, logged_in=True)


@app.route('/add', methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        new_boardgame = Boardgame(
            owner=current_user.id,
            name=request.form.get('name'),
            img=request.form.get('img_link')
            
        )
        db.session.add(new_boardgame)
        db.session.commit()
        return redirect(url_for("collection"))
    
    return render_template("add.html", name=current_user.name, logged_in=True)

@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    boardgame_id = request.args.get("id")
    boardgame = Boardgame.query.get(boardgame_id)
    if request.method == "POST":
        boardgame.img = request.form.get('img_link')
        boardgame.name = request.form.get('name')
        db.session.commit()
        return redirect(url_for('collection'))

    return render_template("edit.html", boardgame=boardgame, name=current_user.name, logged_in=True)

@app.route("/delete")
@login_required
def delete():
    boardgame_id = request.args.get('id')

    # DELETE A RECORD BY ID
    boardgame_to_delete = Boardgame.query.get(boardgame_id)
    db.session.delete(boardgame_to_delete)
    db.session.commit()
    return redirect(url_for('collection'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)