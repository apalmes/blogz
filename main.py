from flask import Flask, request, redirect, render_template, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from password_hash import make_pw_hash, check_pw_hash 

app= Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:hello@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'Super_Secret_Key'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(120))
    post_date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner, post_date=None):
        self.title = title
        self.body = body
        if post_date is None:
            post_date = datetime.utcnow()
        self.post_date = post_date
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)


@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blogs', 'index', 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route('/', methods=['POST', 'GET'])
def index():
    users = User.query.all()
    page_title = 'Blogz'
    return render_template('index.html', users=users, page_title=page_title)
    

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Invalid Username', 'error')
            return redirect('/login')
        if user and check_pw_hash(password, user.pw_hash) == False:
            flash('Invalid Password', 'error')
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            return redirect('/newpost')

    page_title = 'Blogz'   
        
    return render_template('login.html', page_title=page_title)

    
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    page_title='Blogz'

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        username_error = ''
        password_error = ''
        verify_error = ''

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            username_error = "That username already exists"

        if (len(username) < 3) or (len(username) > 20) or username == "":
            username_error = "That is not a valid username"
        
        for char in username:
            if char == " ":
                username_error = "That is not a valid username"
            
        if (len(password) < 3) or (len(password) > 20) or password == "":
            password_error = "That is not a valid password"
    
        for char in password:
            if char == " ":
                password_error = 'That is not a valid password'
    
        if (verify != password) or verify == '':
            verify_error="The passwords do not match"
    
        if not username_error and not password_error and not verify_error and not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')

        else:
            return render_template('signup.html', title='Sign-up', username_error=username_error, password_error=password_error, verify_error=verify_error, page_title=page_title)

    return render_template('signup.html', page_title=page_title)
    

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')


@app.route('/blog', methods=['POST', 'GET'])
def blogs():
    users = User.query.all()
    blog_entries = Blog.query.all()
    page_title = 'Blogz'
    main_title = 'Blog Posts'
    
    if request.method == 'GET':
        if 'id' in request.args:
            blog_id = request.args.get('id')
            blog_content= Blog.query.get(blog_id)
            owner = blog_content.owner
            return render_template('post.html', blog_content=blog_content, page_title=page_title, owner=owner)
        
        if 'user' in request.args:
            username = request.args.get('user')
            owner = User.query.filter_by(username=username).first()
            user_post = Blog.query.filter_by(owner=owner).all()
            return render_template('singleUser.html', user_post=user_post, owner=owner, page_title=page_title)


    return render_template('blog.html', main_title=main_title, page_title=page_title, blog_entries=blog_entries, users=users)


@app.route('/newpost', methods=['POST', 'GET'])
def newpost():
    owner = User.query.filter_by(username=session['username']).first()
    if request.method == 'POST':
        title = request.form['title']
        body = request.form ['body']

        if (title == '') or (body == ''):
            flash('Oops, did you forget something...?', 'error')
        else:
            new_blog = Blog(title, body, owner)
            db.session.add(new_blog)
            db.session.commit()
            new_blog = Blog.query.order_by('-id').first()
            new_blog_redirect = new_blog.id
            users = User.query.all()
            return redirect('/blog?id={0}'.format(new_blog_redirect))

    page_title = 'Blogz'
    main_title = 'Add New Blog Entry'

    return render_template('newpost.html', page_title=page_title, main_title=main_title)


if __name__ == '__main__':
    app.run()