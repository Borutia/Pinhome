from flask import Flask
from authorization.views import authorization
from authorization.database import db_session
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.register_blueprint(authorization, url_prefix='/authorization')


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    app.run(debug=True)
