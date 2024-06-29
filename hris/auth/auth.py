from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from hris.auth.forms import *
from hris.models import *

auth_bp = Blueprint('auth_bp', __name__,  template_folder='templates',
    static_folder='static', static_url_path='static')

@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('login', methods=['GET', 'POST'])
def login():
   
   login_form = LoginForm()

   if current_user.is_authenticated:
        return redirect(url_for('home_bp.home'))

   if login_form.validate_on_submit():
      attempted_user_email = Users.query.filter_by(company_email=login_form.company_email.data).first()

      if attempted_user_email is not None:
         if attempted_user_email and attempted_user_email.verify_password(
            attempted_password = login_form.password.data
         ):
            login_user(attempted_user_email)

            flash(f'{attempted_user_email.company_email} logged in successfully.',
                     category='success')
            return redirect(url_for('home_bp.home'))
         else:
            flash("Email and password didn't match. Please try again", category='danger')
      else:
         flash(f'This account is not registered in the system.', category='info')

   return render_template("login.html", login_form=login_form)


@auth_bp.route('/logout')
@login_required
def logout():
   flash(f'The user was logged out successful!y!', category='info')
   logout_user()
   return redirect(url_for('auth_bp.login'))

