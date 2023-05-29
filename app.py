from flask import Flask,redirect, url_for, request
from oauthlib.oauth2 import WebApplicationClient
from flask_migrate import Migrate
import os 
import json
import requests
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from models import db,UserModel


GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)
# Flask app instance
app = Flask(__name__)

# App Configuration
app.config['JWT_SECRET_KEY'] = 'super-secret-key'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Connect to the database
def connectDB(app):
    try:
        print('Connecting to db ....')
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:123456@localhost:5432/googleAuth"
        db.init_app(app)
        migrate = Migrate(app, db)
        print('Connected to db')
    except:
        print('Cannot connect to DB')

connectDB(app)

# 
login_manager = LoginManager()
login_manager.init_app(app)
client = WebApplicationClient('871480060178-uq0ol8im4slsjtrv60ghr6qi3r74iqud.apps.googleusercontent.com')

# Googleusercontent
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@login_manager.user_loader
def load_user(user_id):
    return UserModel.get(user_id)

@app.route('/')
def hello():
    return "API IS WORKING CORRECTLY"

@app.route("/google_login")
def google_login():
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )

    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=('871480060178-uq0ol8im4slsjtrv60ghr6qi3r74iqud.apps.googleusercontent.com', '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'),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    userinfo = userinfo_response.json()

    # Add user to db if not exists already
    user = UserModel.query.filter_by(email=userinfo['email']).first()

    if not user:
        user = UserModel(
            name=userinfo['name'],
            email=userinfo['email'],
            profile = userinfo['picture']
        )
        db.session.add(user)
        db.session.commit()

    return f"Hello {userinfo['name']}, you are now logged in with the email {userinfo['email']}"


if __name__ == '__main__':
    app.run(debug=True)