from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Import and register blueprints
    from .routes.main_routes import main_bp
    from .routes.auth_routes import auth_bp
    from .routes.check_up_routes import check_up_bp
    from .routes.appointment_routes import appointment_bp
    from .routes.admin_routes import admin_bp
    from .routes.doctor_routes import doctor_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(check_up_bp)
    app.register_blueprint(appointment_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)

    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User  # Local import to avoid circular import
        return User.query.get(int(user_id))

    login_manager.login_view = 'auth.login'

    return app
