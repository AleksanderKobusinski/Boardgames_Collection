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


##CREATE TABLES
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    avatar = db.Column(db.String(1000))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

class Boardgame(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer)
    name = db.Column(db.String(1000))
    img = db.Column(db.String(1000))
    year = db.Column(db.Integer)
    level = db.Column(db.Integer)
    minPlayers = db.Column(db.Integer)
    maxPlayers = db.Column(db.Integer)
    time = db.Column(db.String(100))
    rate = db.Column(db.Integer)

class Following(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100))
    following = db.Column(db.Integer)

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
            flash("Alredy_register")
            return redirect(url_for('register'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            avatar = "https://www.sibberhuuske.nl/wp-content/uploads/2016/10/default-avatar.png",
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
            flash("user")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("password")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('collection'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/collection')
@login_required
def collection():
    users_boardgames = Boardgame.query.filter_by(owner=current_user.id).order_by(Boardgame.rate.desc()).all()
    users_followings = Following.query.filter_by(user=current_user.id).all()
    followings_list = []
    for following in users_followings:
        followings_list.append(User.query.filter_by(id=following.following).first())
    return render_template("collection.html", name=current_user.name, avatar=current_user.avatar, boardgames=users_boardgames, followings=followings_list, logged_in=True)

@app.route('/following/<id>')
@login_required
def following(id):
    User.query.filter_by(id=id).first().name
    users_boardgames = Boardgame.query.filter_by(owner=id).order_by(Boardgame.rate.desc()).all()
    users_followings = Following.query.filter_by(user=current_user.id).all()
    followings_list = []
    for following in users_followings:
        followings_list.append(User.query.filter_by(id=following.following).first())
    return render_template("following.html", name=current_user.name, avatar=current_user.avatar, boardgames=users_boardgames, followings=followings_list, owner=User.query.filter_by(id=id).first().name, logged_in=True)


@app.route('/add', methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        new_boardgame = Boardgame(
            owner = current_user.id,
            name = request.form.get('name'),
            img = request.form.get('img_link'),
            year = request.form.get('year'),
            level = request.form.get('level'),
            minPlayers = request.form.get('minPlayers'),
            maxPlayers = request.form.get('maxPlayers'),
            time = request.form.get('time'),
            rate = request.form.get('rate')
        )
        db.session.add(new_boardgame)
        db.session.commit()
        return redirect(url_for("collection"))
    
    return render_template("add.html", name=current_user.name, avatar=current_user.avatar, logged_in=True)

@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    boardgame_id = request.args.get("id")
    boardgame = Boardgame.query.get(boardgame_id)
    if request.method == "POST":
        boardgame.img = request.form.get('img_link')
        boardgame.name = request.form.get('name')
        boardgame.year = request.form.get('year')
        boardgame.level = request.form.get('level')
        boardgame.minPlayers = request.form.get('minPlayers')
        boardgame.maxPlayers = request.form.get('maxPlayers')
        boardgame.time = request.form.get('time')
        boardgame.rate = request.form.get('rate')
        db.session.commit()
        return redirect(url_for('collection'))

    return render_template("edit.html", boardgame=boardgame, name=current_user.name, avatar=current_user.avatar, logged_in=True)

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


@app.route('/addfollowing', methods=["GET", "POST"])
@login_required
def addfollowing():
    if request.method == "POST":
        new_following = User.query.filter_by(email=request.form.get('email')).first()
        all_followings = Following.query.filter_by(user=current_user.id).all()
        if current_user.id == new_following.id:
                flash("Is_you")
                return redirect(url_for('addfollowing'))
        for following in all_followings:
            if User.query.filter_by(id=following.following).first().id == new_following.id:
                flash("Alredy_is")
                return redirect(url_for('addfollowing'))
        new_following = Following(
            user = current_user.id,
            following = new_following.id
        )
        db.session.add(new_following)
        db.session.commit()
        return redirect(url_for("collection"))
    
    return render_template("addfollowing.html", name=current_user.name, avatar=current_user.avatar, logged_in=True)

@app.route("/deletefollowing")
@login_required
def deletefollowing():
    following_id = request.args.get('id')
    following = Following.query.filter_by(user=current_user.id, following=following_id).first()
    following_to_delete = Following.query.get(following.id)
    # DELETE A RECORD BY ID
    db.session.delete(following_to_delete)
    db.session.commit()
    return redirect(url_for('collection'))

if __name__ == "__main__":
    app.run(debug=True)