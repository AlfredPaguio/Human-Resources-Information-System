from datetime import date
from sqlalchemy.exc import IntegrityError
from hris import models as m
from hris import db
from sqlalchemy.sql import func


def delete_all_records():
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print(f"Clearing table {table}")
        db.session.execute(table.delete())
    db.session.commit()


def create_default_data():

   delete_all_records()

   admin_user = m.Users(
      name="Admin",
      company_email="admin@email.com",
      password_hash="$2b$12$7GeFLc7mQRY1JjEAbDQ0ruv/HPeeG4CX1WyKAaS.yD5gJ2k3Vo712",
      access="Admin",
      date_created=func.current_date(),
   )

   db.session.add(admin_user)
   db.session.commit()

   departments = [
      m.Departments(
         department_name="HR", manager="Alice Smith", description="Human Resources"
      ),
      m.Departments(
         department_name="IT",
         manager="Bob Brown",
         description="Information Technology",
      ),
      m.Departments(
         department_name="Finance",
         manager="Carol Johnson",
         description="Finance Department",
      ),
   ]

   db.session.add_all(departments)
   db.session.commit()

   positions = [
      m.Positions(
         position_name="HR Manager",
         description="Manages HR",
         position_status="Full",
         department_id=departments[0].id,
      ),
      m.Positions(
         position_name="IT Manager",
         description="Manages IT",
         position_status="Full",
         department_id=departments[1].id,
      ),
      m.Positions(
         position_name="Finance Manager",
         description="Manages Finance",
         position_status="Full",
         department_id=departments[2].id,
      ),
      m.Positions(
         position_name="HR Assistant",
         description="Assists HR",
         position_status="Hiring",
         department_id=departments[0].id,
      ),
      m.Positions(
         position_name="IT Support",
         description="Supports IT",
         position_status="Hiring",
         department_id=departments[1].id,
      ),
      m.Positions(
         position_name="Accountant",
         description="Handles accounts",
         position_status="Hiring",
         department_id=departments[2].id,
      ),
   ]

   db.session.add_all(positions)
   db.session.commit()
    
   admin_employee_info = m.EmployeeInfo(
               last_name='Admin',
               first_name='Admin',
               middle_name='Admin',
               gender='Male',
               birth_date=date(2000, 1, 1), 
               civil_status='Single',  
               mobile='09123456789', 
               email='admin@email.com',
               address='123 Admin St',
               emergency_name='Admin Emergency Contact',
               emergency_contact='09987654321',
               emergency_relationship='Self',
               tin='123-14123-2323',
               SSS='44-23231431-0',
               phil_health=f'14-66454542141-5',
               pag_ibig=f'5151-1124-2333',
               date_created=func.current_date()
         )
         
   db.session.add(admin_employee_info)
   db.session.commit()

    # admin_employment_info = m.EmploymentInfo(
    #    description='Default employment info for admin',
    #    start_date=date(2000, 1, 1),
    #    status='Hired',
    #    employee_id=admin_employee_info.id
    # )

    # db.session.add(admin_employment_info)
    # db.session.commit()
