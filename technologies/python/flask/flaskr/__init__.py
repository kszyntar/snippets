# -*- coding: utf-8 -*-


''' App Creation
'''

import os
import logging
import atexit

from flask import Flask
from flaskr import dynatrace
from flaskr.dynatrace_middleware import DynatraceWSGIMiddleware

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""

    # initialize the OneAgent Python SDK
    if dynatrace.sdk_init():
        atexit.register(dynatrace.sdk_shutdown)

    # create the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY='dev',
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Do this after configuration is applied
    app.wsgi_app = DynatraceWSGIMiddleware(
        app.wsgi_app, app.name,
        virtual_host=app.config.get('SERVER_NAME'),
        context_root=app.config.get('APPLICATION_ROOT'))

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    # register the database commands
    from flaskr import db
    db.init_app(app)

    # apply the blueprints to the app
    from flaskr import auth, blog
    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    app.before_request(dynatrace.start_web_request)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule('/', endpoint='index')

    return app
