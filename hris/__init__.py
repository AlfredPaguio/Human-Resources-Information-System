import os
from os import path

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()
DB_NAME = "hris"
UPLOAD_FOLDER = "static/upload"

app = Flask(__name__)

app.config["SECRET_KEY"] = "fa282f581ec1d84bc02c6f34d4da17a2"
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "images", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 16MB in bytes

# for sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_NAME}.db"

# for postgres
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://sgvfendbdncwqh:607684ab44215243dd4a6dcd9e41fe17b6bc042736c232ed00c431ab50e0b313@ec2-3-217-146-37.compute-1.amazonaws.com:5432/dc7t8n0sm0dtec"

# for mysql
# app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql://root:@localhost:3306/{DB_NAME}"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db.init_app(app)
bcrypt.init_app(app)
migrate.init_app(app, db)
login_manager.login_view = "auth_bp.login"
login_manager.login_message_category = "info"
login_manager.init_app(app)

# import blueprints here to avoid circular imports
from .announcements.announcement import announcement_bp  # noqa: E402
from .attendance.attendance import attendance_bp  # noqa: E402
from .auth.auth import auth_bp  # noqa: E402
from .departments.departments import departments_bp  # noqa: E402
from .employees.employees import employees_bp  # noqa: E402
from .home.home import home_bp  # noqa: E402
from .payroll.payroll import payroll_bp  # noqa: E402
from .payslips.payslips import payslips_bp  # noqa: E402
from .profile.profile import profile_bp  # noqa: E402
from .salaries.salaries import salaries_bp  # noqa: E402
from .schedules.schedules import schedules_bp  # noqa: E402

# register Blueprints
app.register_blueprint(home_bp, url_prefix="/")
app.register_blueprint(auth_bp, url_prefix="/")
app.register_blueprint(departments_bp, url_prefix="/")
app.register_blueprint(employees_bp, url_prefix="/")
app.register_blueprint(announcement_bp, url_prefix="/")
app.register_blueprint(attendance_bp, url_prefix="/")
app.register_blueprint(salaries_bp, url_prefix="/")
app.register_blueprint(payroll_bp, url_prefix="/")
app.register_blueprint(payslips_bp, url_prefix="/")
app.register_blueprint(profile_bp, url_prefix="/")
app.register_blueprint(schedules_bp, url_prefix="/")


# from .models import Users, EmployeeInfo, Attendance, Leave, EmploymentInfo, Positions, Departments

# for sqlite
if not path.exists('db/' + DB_NAME):
   with app.app_context():
      db.create_all()

# for mysql
# uncomment when creating new db.
# with app.app_context():
#     db.create_all()
