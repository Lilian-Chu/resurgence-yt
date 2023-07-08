import os

from flask import Flask

def create_app(test_config=None):
    # App configurations
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'resurgence.sqlite')
    )

    if test_config is None:
        # When not testing, load the instance config
        app.config.from_pyfile('config.py', silent=True)
    else:
        # When testing, load the test config
        app.config.from_mapping(test_config)
    
    # Check if the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # A simple page that print hello world
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    
    from resurgence import db
    db.init_app(app)
    
    from . import home
    from . import get_video_info
    app.register_blueprint(home.bp)
    app.register_blueprint(get_video_info.bp)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import user
    app.register_blueprint(user.bp)

    app.add_url_rule("/", endpoint="index")

    return app
