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

class Boardgame(db.Model):
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

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100))
    friend = db.Column(db.Integer)
    status = db.Column(db.String(10))

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
    users_friends = Friendship.query.filter_by(user=current_user.id).all()
    friends_list_accepted = []
    friends_list_waiting = []
    for friend in users_friends:
        if friend.status == "accepted":
            friends_list_accepted.append(User.query.filter_by(id=friend.friend).first())
        else:
            friends_list_waiting.append(User.query.filter_by(id=friend.friend).first())
    return render_template("collection.html", name=current_user.name, avatar=current_user.avatar, boardgames=users_boardgames, friends_accepted=friends_list_accepted, friends_waiting=friends_list_waiting, logged_in=True)

@app.route('/friend/<id>')
@login_required
def friend(id):
    User.query.filter_by(id=id).first().name
    users_boardgames = Boardgame.query.filter_by(owner=id).order_by(Boardgame.rate.desc()).all()
    users_friends = Friendship.query.filter_by(user=current_user.id).all()
    friends_list_accepted = []
    friends_list_waiting = []
    for friend in users_friends:
        if friend.status == "accepted":
            friends_list_accepted.append(User.query.filter_by(id=friend.friend).first())
        else:
            friends_list_waiting.append(User.query.filter_by(id=friend.friend).first())
    return render_template("friend.html", name=current_user.name, avatar=current_user.avatar, boardgames=users_boardgames, friends_accepted=friends_list_accepted, friends_waiting=friends_list_waiting, owner=User.query.filter_by(id=id).first().name, logged_in=True)


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

@app.route('/addfriend', methods=["GET", "POST"])
@login_required
def addfriend():
    if request.method == "POST":
        new_friend = User.query.filter_by(email=request.form.get('email')).first()
        all_friends = Friendship.query.filter_by(user=current_user.id).all()
        if current_user.id == new_friend.id:
                flash("Is_you")
                return redirect(url_for('addfriend'))
        for friend in all_friends:
            if User.query.filter_by(id=friend.friend).first().id == new_friend.id:
                flash("Alredy_is")
                return redirect(url_for('addfriend'))
        new_friendship = Friendship(
            user = new_friend.id,
            friend = current_user.id,
            status = "waiting"
        )
        db.session.add(new_friendship)
        db.session.commit()
        return redirect(url_for("collection"))
    
    return render_template("addfriend.html", name=current_user.name, avatar=current_user.avatar, logged_in=True)

@app.route("/acceptfriend")
@login_required
def acceptfriend():
    friend_id = request.args.get('id')
    friendship = Friendship.query.filter_by(user=current_user.id, friend=friend_id).first()
    friendship_to_accept = Friendship.query.get(friendship.id)
    friendship_to_accept.status = "accepted"
    new_friendship = Friendship(
        user = friend_id,
        friend = current_user.id,
        status = "accepted"
    )
    db.session.add(new_friendship)
    db.session.commit()
    return redirect(url_for('collection'))

@app.route("/declinefriend")
@login_required
def declinefriend():
    friend_id = request.args.get('id')
    friendship = Friendship.query.filter_by(user=current_user.id, friend=friend_id).first()
    friendship_to_delete = Friendship.query.get(friendship.id)

    # DELETE A RECORD BY ID
    db.session.delete(friendship_to_delete)
    db.session.commit()
    return redirect(url_for('collection'))

@app.route("/deletefriend")
@login_required
def deletefriend():
    friend_id = request.args.get('id')
    friendship = Friendship.query.filter_by(user=current_user.id, friend=friend_id).first()
    friendship2 = Friendship.query.filter_by(user=friend_id, friend=current_user.id).first()
    friendship_to_delete = Friendship.query.get(friendship.id)
    friendship_to_delete2 = Friendship.query.get(friendship2.id)
    # DELETE A RECORD BY ID
    db.session.delete(friendship_to_delete)
    db.session.delete(friendship_to_delete2)
    db.session.commit()
    return redirect(url_for('collection'))

if __name__ == "__main__":
    app.run(debug=True)