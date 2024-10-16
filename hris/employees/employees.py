import os
import pathlib
import random
import string

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from password_strength import PasswordPolicy
from werkzeug.utils import secure_filename

from hris.models import *

from .forms import *

employees_bp = Blueprint(
    "employees_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="employee/static",
)


@employees_bp.route("/employees/get_positions")
@login_required
def get_positions():
    department_id = request.args.get("department_id")

    positions = (
        db.session.query(Positions)
        .filter(Positions.department_id == department_id)
        .filter(Positions.position_status == "Hiring")
        .all()
    )
    # positions = Positions.query.filter_by(department_id=department_id).all()
    positions = [
        {"id": position.id, "name": position.position_name} for position in positions
    ]
    return jsonify(positions)


@employees_bp.route("/employees", methods=["GET"])
@login_required
def employees():
    delete_employee_modal = DeleteEmployeeModal()

    # employees = db.session.query(EmployeeInfo.id, EmployeeInfo.last_name, EmployeeInfo.first_name,
    #    EmployeeInfo.middle_name, Positions.position_name, Departments.department_name,
    #    EmploymentInfo.start_date, EmploymentInfo.salary_id, EmploymentInfo.status, Salaries.daily_rate)\
    #    .join(EmployeeInfo, EmployeeInfo.id == EmploymentInfo.employee_id)\
    #    .join(Positions, Positions.id == EmployeeInfo.position_id)\
    #    .join(Departments, Departments.id == Positions.department_id)\
    #    .join(Salaries, Salaries.id == EmploymentInfo.salary_id).all()

    employees = (
       db.session.query(
            EmployeeInfo.id,
            EmployeeInfo.last_name,
            EmployeeInfo.first_name,
            EmployeeInfo.middle_name,
            Positions.position_name,
            Departments.department_name,
            EmploymentInfo.start_date,
            EmploymentInfo.salary_id,
            EmploymentInfo.status,
            Salaries.daily_rate,
        )
        .join(EmploymentInfo, EmployeeInfo.id == EmploymentInfo.employee_id)
        .outerjoin(Positions, Positions.id == EmployeeInfo.position_id)
        .outerjoin(Departments, Departments.id == Positions.department_id)
        .outerjoin(Salaries, Salaries.id == EmploymentInfo.salary_id)
        .filter(EmployeeInfo.id != 1)
        .all() 
    )

    return render_template(
        "employees.html",
        employees=employees,
        delete_employee_modal=delete_employee_modal,
    )


@employees_bp.route("/employees/add_employee", methods=["GET", "POST"])
@login_required
def add_employee():
    add_employee = EmployeeForm()

    departments = db.session.query(Departments).all()
    salaries = db.session.query(Salaries).all()

    if request.method == "POST":
        if add_employee.validate_on_submit:

            if add_employee.validate_email_address(add_employee.company_email):
                flash(
                    "Company email already exist! Please chooce a different company email",
                    category="danger",
                )
            else:

                policy = PasswordPolicy.from_names(
                    length=8,  # min length: 8
                    uppercase=1,  # need min. 1 uppercase letters
                    numbers=1,  # need min. 1 digits
                    special=1,  # need min. 1 special characters
                    nonletters=1,  # need min. 1 non-letter characters (digits, specials, anything)
                )

                if len(policy.test(add_employee.password1.data)) == 0:
                    new_employee_info = EmployeeInfo(
                        last_name=add_employee.last_name.data,
                        first_name=add_employee.first_name.data,
                        middle_name=add_employee.middle_name.data,
                        gender=add_employee.gender.data.capitalize(),
                        birth_date=datetime.strptime(
                            add_employee.birth_date.data, "%Y-%m-%d"
                        ).date(),
                        civil_status=add_employee.civil_status.data.capitalize(),
                        mobile=add_employee.mobile.data,
                        email=add_employee.email.data,
                        address=add_employee.address.data,
                        emergency_name=add_employee.emergency_name.data,
                        emergency_contact=add_employee.emergency_contact.data,
                        emergency_relationship=add_employee.emergency_relationship.data,
                        tin=add_employee.tin.data,
                        SSS=add_employee.sss.data,
                        phil_health=add_employee.phil_health.data,
                        pag_ibig=add_employee.pag_ibig.data,
                        position_id=add_employee.positions.data,
                    )

                    db.session.add(new_employee_info)
                    db.session.flush()

                    new_employment_info = EmploymentInfo(
                        description=add_employee.description.data,
                        start_date=datetime.strptime(
                            add_employee.start_date.data, "%Y-%m-%d"
                        ).date(),
                        status=add_employee.status.data.capitalize(),
                        employee_id=new_employee_info.id,
                        salary_id=add_employee.salary_rate.data,
                    )

                    db.session.add(new_employment_info)
                    db.session.flush()

                    new_employee_account = Users(
                        name=new_employee_info.fullname,
                        company_email=add_employee.company_email.data,
                        password=add_employee.password1.data,
                        employee_id=new_employee_info.id,
                    )

                    file = request.files["image_path"]

                    if file:

                        filename = secure_filename(file.filename)

                        random_string = "".join(
                            random.choices(string.ascii_lowercase + string.digits, k=10)
                        )
                        filename = random_string + pathlib.Path(filename).suffix

                        filepath = os.path.join(
                            current_app.config["UPLOAD_FOLDER"], filename
                        )
                        file.save(filepath)

                        rel_path = os.path.join("images", "uploads", filename).replace(
                            "\\", "/"
                        )
                        new_employee_account.image_path = rel_path

                    db.session.add(new_employee_account)
                    db.session.commit()

                    flash("Employee record submitted!", category="success")
                    return redirect(url_for("employees_bp.employees"))
                else:
                    for e in policy.test(add_employee.password1.data):
                        flash(f"Password needs atleast: {e}", category="danger")

        if add_employee.errors != {}:
            for err_msg in add_employee.errors.values():
                flash(
                    f"There is an error with adding new employee: {err_msg}",
                    category="danger",
                )
            return redirect(url_for("employees_bp.add_employee"))

    return render_template(
        "add_employee.html",
        add_employee=add_employee,
        departments=departments,
        salaries=salaries,
    )


@employees_bp.route(
    "/employees/<int:employee_id>/<string:employee_name>", methods=["GET", "POST"]
)
@login_required
def manage_employee(employee_name, employee_id):
    selected_employee = (
        db.session.query(Users, EmployeeInfo, EmploymentInfo, Positions, Departments)
        .join(EmploymentInfo)
        .join(Users)
        .join(Positions)
        .join(Departments)
        .filter(EmployeeInfo.id == employee_id)
        .first()
    )

    user, employee_info, employment_info, position, department = selected_employee

    departments = db.session.query(Departments).all()
    salaries = db.session.query(Salaries).all()
    positions = department.getPositions

    manage_employee = EmployeeForm(
        # employee info
        last_name=employee_info.last_name,
        first_name=employee_info.first_name,
        middle_name=employee_info.middle_name,
        gender=employee_info.gender,
        birth_date=employee_info.birth_date,
        civil_status=employee_info.civil_status,
        mobile=employee_info.mobile,
        email=employee_info.email,
        address=employee_info.address,
        tin=employee_info.tin,
        sss=employee_info.SSS,
        phil_health=employee_info.phil_health,
        pag_ibig=employee_info.pag_ibig,
        emergency_name=employee_info.emergency_name,
        emergency_contact=employee_info.emergency_contact,
        emergency_relationship=employee_info.emergency_relationship,
        # Employment Profile
        description=employment_info.description,
        salary_rate=employment_info.salary_id,
        start_date=employment_info.start_date,
        end_date=employment_info.end_date,
        status=employment_info.status.value,
        positions=employee_info.position_id,
    )

    department_id = position.department_id
    position_id = employee_info.position_id

    if request.method == "POST":

        if manage_employee.validate_on_submit:
            employee_info.last_name = manage_employee.last_name.data
            employee_info.first_name = manage_employee.first_name.data
            employee_info.middle_name = manage_employee.middle_name.data
            employee_info.gender = manage_employee.gender.data.capitalize()
            employee_info.birth_date = manage_employee.birth_date.data
            employee_info.civil_status = manage_employee.civil_status.data.capitalize()
            employee_info.mobile = manage_employee.mobile.data
            employee_info.email = manage_employee.email.data
            employee_info.address = manage_employee.address.data
            employee_info.tin = manage_employee.tin.data
            employee_info.sss = manage_employee.sss.data
            employee_info.phil_health = manage_employee.phil_health.data
            employee_info.pag_ibig = manage_employee.pag_ibig.data
            employee_info.emergency_name = manage_employee.emergency_name.data
            employee_info.emergency_contact = manage_employee.emergency_contact.data
            employee_info.emergency_relationship = (
                manage_employee.emergency_relationship.data
            )
            employee_info.position_id = manage_employee.positions.data

            employment_info.description = manage_employee.description.data
            employment_info.salary_id = manage_employee.salary_rate.data
            employment_info.start_date = manage_employee.start_date.data
            employment_info.end_date = (
                None
                if manage_employee.status.data == "hired"
                else manage_employee.end_date.data
            )
            employment_info.status = manage_employee.status.data

            db.session.commit()
            flash(f"{employee_name}'s profile updated successfully", category="success")
            return redirect(url_for("employees_bp.employees"))

    return render_template(
        "manage_employee.html",
        manage_employee=manage_employee,
        departments=departments,
        positions=positions,
        department_id=department_id,
        position_id=position_id,
        employee_info=employee_info,
        user=user,
        salaries=salaries,
        employee_name=employee_name,
        employee_id=employee_id,
    )


@employees_bp.route(
    "/employees/<int:employee_id>/<string:employee_name>/account_settings",
    methods=["GET", "POST"],
)
@login_required
def manage_employee_account(employee_name, employee_id):
    account_form = AccountForm()

    if request.method == "POST":
        account_form = AccountForm(request.form)
        attempted_password = account_form.password1.data

        user_account = Users.query.filter_by(employee_id=employee_id).first()

        if account_form.validate_on_submit():
            # Upload
            file = request.files["image_path"]

            if file:
                filename = secure_filename(file.filename)

                if user_account.image_path:
                    try:
                        # os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], pathlib.Path(user_account.image_path).name).replace('\\', '/'))
                        os.remove(
                            pathlib.PurePath(
                                current_app.config["UPLOAD_FOLDER"],
                                pathlib.Path(user_account.image_path).name,
                            )
                        )
                        print(
                            f"The file {pathlib.Path(user_account.image_path).name} is successfully deleted"
                        )
                    except FileNotFoundError as e:
                        print(
                            f"{pathlib.Path(user_account.image_path).name} not found!"
                        )

                # filename = (str(user_account.id) + file_extension)
                random_string = "".join(
                    random.choices(string.ascii_lowercase + string.digits, k=10)
                )
                filename = random_string + pathlib.Path(filename).suffix
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)

                rel_path = os.path.join("images", "uploads", filename).replace(
                    "\\", "/"
                )
                user_account.image_path = rel_path
                db.session.commit()

                flash(f"Updated Account Profile Picture!", category="success")

            if account_form.password1.data != "" and account_form.password2.data != "":
                policy = PasswordPolicy.from_names(
                    length=8,  # min length: 8
                    uppercase=1,  # need min. 1 uppercase letters
                    numbers=1,  # need min. 1 digits
                    special=1,  # need min. 1 special characters
                    nonletters=1,  # need min. 1 non-letter characters (digits, specials, anything)
                )

                if attempted_password and user_account.verify_password(
                    attempted_password
                ):
                    flash(
                        "New password can't be the same as the old password.",
                        category="danger",
                    )

                else:
                    if len(policy.test(attempted_password)) == 0:
                        user_account.password = attempted_password
                        db.session.commit()

                        flash(f"Updated Account Password!", category="success")
                    else:
                        for e in policy.test(attempted_password):
                            flash(f"Password needs atleast: {e}", category="danger")

            return redirect(
                url_for(
                    "employees_bp.manage_employee_account",
                    employee_id=employee_id,
                    employee_name=employee_name,
                )
            )

        if account_form.errors != {}:
            for err_msg in account_form.errors.values():
                if err_msg == ["Field must be equal to password1."]:
                    flash(
                        f"There is an error updating the account: ['Password didn't match.']",
                        category="danger",
                    )
                else:
                    flash(
                        f"There is an error with updating the account: {err_msg}",
                        category="danger",
                    )

            return redirect(
                url_for(
                    "employees_bp.manage_employee_account",
                    employee_id=employee_id,
                    employee_name=employee_name,
                )
            )

    if request.method == "GET":
        selected_employee = Users.query.filter_by(employee_id=employee_id).first()

        return render_template(
            "manage_employee_account.html",
            selected_employee=selected_employee,
            account_form=account_form,
            employee_id=employee_id,
            employee_name=employee_name,
        )


@employees_bp.route(
    "/employees/delete_employee/<int:employee_id>", methods=["GET", "POST"]
)
@login_required
def delete_employee(employee_id):

    if request.method == "POST":
        remove_employee = EmployeeInfo.query.filter_by(id=employee_id).delete()
        db.session.commit()
        flash("User deleted!", category="danger")
        return redirect(url_for("employees_bp.employees"))

    return render_template("employees.html")
