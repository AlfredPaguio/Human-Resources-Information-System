import os
import pathlib
import random
import string

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_required, logout_user
from password_strength import PasswordPolicy
from werkzeug.utils import secure_filename

from hris.employees.forms import *
from hris.models import *

profile_bp = Blueprint('profile_bp', __name__,  template_folder='templates',
    static_folder='static', static_url_path='/profile_bp.static')


@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        employee_to_update = EmployeeInfo.query.filter_by(id = current_user.id).first()

        employee_form = EmployeeForm(request.form)

        if employee_form.validate_on_submit:
            
            employee_to_update.last_name = employee_form.last_name.data
            employee_to_update.first_name = employee_form.first_name.data
            employee_to_update.middle_name = employee_form.middle_name.data
            employee_to_update.gender = employee_form.gender.data.capitalize()
            employee_to_update.birth_date = employee_form.birth_date.data
            employee_to_update.civil_status = employee_form.civil_status.data.capitalize()
            employee_to_update.mobile = employee_form.mobile.data
            employee_to_update.email = employee_form.email.data
            employee_to_update.address = employee_form.address.data
            employee_to_update.emergency_name = employee_form.emergency_name.data
            employee_to_update.emergency_contact = employee_form.emergency_contact.data
            employee_to_update.emergency_relationship = employee_form.emergency_relationship.data

            db.session.commit()

            flash(f'Employee Profile Updated!', category='success')

            return redirect(url_for('profile_bp.profile'))
              
        if employee_form.errors != {}:

            for err_msg in employee_form.errors.values():
                flash(f'There is an error with updating the account: {err_msg}', category='danger')
            return redirect(url_for('profile_bp.profile'))
        
    if request.method == 'GET':
        selected_employee = db.session.query(Users, EmployeeInfo, EmploymentInfo, Positions, Departments)\
            .join(EmploymentInfo).join(Users).join(Positions).join(Departments)\
            .filter(EmployeeInfo.id == current_user.employee_id).first()

        salaries = db.session.query(Salaries).all()

        if selected_employee:
            user, employee_info, employment_info, position, department = selected_employee
        else:
            flash('Employee not found.', 'error')
            print(f'Employee: {selected_employee}')
            return redirect(url_for('announcement_bp.announcements'))
        
        employee_form = EmployeeForm(
            #users
            image_path = user.image_path,
            company_email = user.company_email,
            access = user.access.value,
            
            #employee info
            last_name = employee_info.last_name,
            first_name = employee_info.first_name,
            middle_name = employee_info.middle_name,
            gender = employee_info.gender,
            birth_date = employee_info.birth_date,
            civil_status = employee_info.civil_status,
            mobile = employee_info.mobile,
            email = employee_info.email,
            address = employee_info.address,
            tin = employee_info.tin,
            sss = employee_info.SSS,
            phil_health = employee_info.phil_health,
            pag_ibig = employee_info.pag_ibig,
            emergency_name = employee_info.emergency_name,
            emergency_contact = employee_info.emergency_contact,
            emergency_relationship = employee_info.emergency_relationship,

            #Employment Profile
            description = employment_info.description,
            salary_rate = employment_info.salary_id,
            start_date = employment_info.start_date,
            end_date = employment_info.end_date,
            status = employment_info.status.value,
            position = employee_info.position_id
        )

        return render_template('profile.html', user=user,
                            employee_info=employee_info,
                            employment_info=employment_info,
                            position=position,
                            department=department,
                            employee_form=employee_form,
                            salaries=salaries)



@profile_bp.route('/profile/<int:employee_id>/update_account', methods=['GET', 'POST'])
@login_required
def account_settings(employee_id):
    if request.method == 'POST':
        account_form = AccountForm(request.form)
        attempted_password = account_form.password1.data
        old_password = account_form.old_password.data

        user_account = Users.query.filter_by(id = employee_id).first()

        if account_form.validate_on_submit():
            #Upload
            file = request.files['image_path']
            
            if file:
                filename = secure_filename(file.filename)
                if (user_account.image_path):
                     print(pathlib.Path(user_account.image_path).name)
                     try:
                        os.remove(pathlib.PurePath(current_app.config['UPLOAD_FOLDER'], pathlib.Path(user_account.image_path).name))
                        print(f'The file on {pathlib.Path(user_account.image_path)} is successfully deleted')
                     except FileNotFoundError as e:
                        print(f"{pathlib.Path(user_account.image_path).name} not found!")

                #filename = (str(user_account.id) + pathlib.Path(filename).suffix)
                random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                filename = (random_string + pathlib.Path(filename).suffix)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                
                file.save(filepath)
               
                rel_path = os.path.join('images', 'uploads', filename).replace('\\', '/')
                user_account.image_path = rel_path
                db.session.commit()

                flash(f'Updated Account Profile Picture!', category='success')

            #Password
            if old_password != '':
                if old_password != user_account.verify_password(attempted_password):
                    if account_form.password1.data != '' and account_form.password2.data != '':
                        policy = PasswordPolicy.from_names(
                            length=8,  # min length: 8
                            uppercase=1,  # need min. 1 uppercase letters
                            numbers=1,  # need min. 1 digits
                            special=1,  # need min. 1 special characters
                            nonletters=1,  # need min. 1 non-letter characters (digits, specials, anything)
                        )

                        if attempted_password and user_account.verify_password(attempted_password):
                            flash("New password can't be the same as the old password.", category='danger')

                        else:
                            if len(policy.test(attempted_password)) == 0:
                                user_account.password = attempted_password
                                db.session.commit()

                                session.clear()
                                logout_user()
                                flash(f'Updated Account Password! Please Login Again.', category='success')
                                return redirect(url_for('auth_bp.login'))
                            else:
                                for e in policy.test(attempted_password):
                                    flash(f'Password needs atleast: {e}', category='danger')
                else:
                    flash(f"Password can't be the same as old password", category='danger')
            elif old_password == '' and attempted_password != '':
                flash(f"Old password can't be empty", category='danger')
            else:
                flash('No changes for password', category='info')
            
            return redirect(url_for('profile_bp.account_settings', employee_id=employee_id))
        
        if account_form.errors != {}:
            for err_msg in account_form.errors.values():
                if err_msg == ['Field must be equal to password1.']:
                    flash(f"There is an error updating the account: ['Password didn't match.']", category='danger')
                else:
                    flash(f'There is an error with updating the account: {err_msg}', category='danger')
            
            return redirect(url_for('profile_bp.account_settings', employee_id=employee_id))
    if request.method == 'GET':  
        account_form = AccountForm()
        selected_employee = Users.query.filter_by(employee_id = current_user.employee_id).first()      
        return render_template('account_settings.html', selected_employee=selected_employee, account_form=account_form)
    