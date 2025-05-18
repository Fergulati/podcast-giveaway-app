from flask import Flask


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_mapping(SECRET_KEY='dev')

    from . import routes
    routes.init_app(app)

    return app
