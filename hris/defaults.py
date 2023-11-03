from hris import models as m
from hris import db
from sqlalchemy.sql import func

def create_default_data():

   admin_user = m.Users(
      name = 'Admin',
      company_email = 'admin@email.com',
      password_hash = '$2b$12$7GeFLc7mQRY1JjEAbDQ0ruv/HPeeG4CX1WyKAaS.yD5gJ2k3Vo712',
      access = 'Admin',
      date_created = func.current_date(),
   )
   #pass 123

   db.session.add(admin_user)
   db.session.commit()