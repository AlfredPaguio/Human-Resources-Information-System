import enum
from datetime import date, datetime

from flask_login import UserMixin
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func

from . import bcrypt, db, login_manager


class USER_TYPES(enum.Enum):
   Employee = "Employee"
   Admin = "Admin"

class STATUS_TYPES(enum.Enum):
   Approved = "Approved"
   Declined = "Declined"
   Pending = "Pending"

class HIRE_TYPES(enum.Enum):
   Hired = "Hired"
   Retired = "Retired"
   Terminated = "Terminated"
   Resigned = "Resigned"

class ATTENDANCE_TYPES(enum.Enum):
   Present = "Present"
   Absent = "Absent"
   Late = "Late"
   Unavailable = "Unavailable"
   On_Leave = "On_Leave"

class LEAVE_TYPES(enum.Enum):
   Sick_Leave = "Sick_Leave"
   SIL = "SIL"
   Maternity_Leave = "Maternity_Leave"
   Paternity_Leave = "Paternity_Leave"
   Vacation_Leave = "Vacation_Leave"
   Parental_Leave = "Parental_Leave"   
   Rehabilitation_Leave = "Rehabilitation_Leave"
   Study_Leave = "Study_Leave"

class POSITION_STATUS(enum.Enum):
   Hiring = "Hiring"
   Full = "Full"

@login_manager.user_loader
def load_user(user_id):
   print(f"Loading user with ID: {user_id}")
   user = Users.query.get(int(user_id))
   if user:
      print(f"User found: {user}")
      print(dir(user))
   else:
      print("User not found.")
   return user

class Users(db.Model, UserMixin):
   # Primary Key
   id = db.Column(db.Integer(), primary_key=True)

   name = db.Column(db.String(length=60), nullable=False)
   image_path = db.Column(db.String(length=50), server_default='images/profile.svg')
   company_email = db.Column(db.String(length=50), nullable=False, unique=True)
   password_hash = db.Column(db.String(length=60), nullable=False)
   access = db.Column(db.Enum(USER_TYPES), nullable=False, default=USER_TYPES.Employee)
   date_created = db.Column(db.Date(), default=func.current_date(), nullable=False)

   # Foreign Keys
   employee_id = db.Column(db.Integer(), db.ForeignKey('employee_info.id', ondelete="CASCADE"))

   # Relationship
   announcement_info = db.relationship('Announcements', backref='announcements')

   @hybrid_property
   def getAnnouncement(self):
      if self.announcement_info:
         return self.announcement_info
      else:
         return None

   @property
   def password(self):
      return self.password

   # Encrypt password
   @password.setter
   def password(self, plain_text_password):
      self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

   def verify_password(self, attempted_password):
      return bcrypt.check_password_hash(self.password_hash, attempted_password)


class Announcements(db.Model):
   # Primary Key
   id = db.Column(db.Integer(), primary_key=True)

   date_created = db.Column(db.Date(), default=func.current_date(), nullable=False)
   announced_by = db.Column(db.String(length=500), nullable=False)
   title = db.Column(db.String(length=500), nullable=False)
   message = db.Column(db.String(length=500) ,nullable=False)

   # Foreign Key
   user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete="CASCADE"))

class EmployeeInfo(db.Model):
   # Primary Key
   id = db.Column(db.Integer(), primary_key=True)

   last_name = db.Column(db.String(length=50), nullable=False)
   first_name = db.Column(db.String(length=50), nullable=False)
   middle_name = db.Column(db.String(length=50), nullable=False)
   gender = db.Column(db.String(length=50), nullable=False)
   birth_date= db.Column(db.Date(), nullable=False)
   civil_status = db.Column(db.String(length=50), nullable=False)
   mobile = db.Column(db.String(length=50), nullable=False)
   email = db.Column(db.String(length=50), nullable=False)
   address = db.Column(db.String(length=50), nullable=False)
   emergency_name = db.Column(db.String(length=50), nullable=False)
   emergency_contact = db.Column(db.String(length=50), nullable=False)
   emergency_relationship = db.Column(db.String(length=50), nullable=False)
   tin = db.Column(db.String(length=50), nullable=True, unique=False) #Temporary
   SSS = db.Column(db.String(length=50), nullable=True, unique=False) #Temporary
   phil_health = db.Column(db.String(length=50), nullable=True, unique=False) #Temporary
   pag_ibig = db.Column(db.String(length=50), nullable=True, unique=False) #Temporary
   date_created = db.Column(db.Date(), default=func.current_date(), nullable=True)

   #Foreign Keys  
   position_id = db.Column(db.Integer(), db.ForeignKey('positions.id'))
   

   #Relationship
   user_info = db.relationship('Users', backref='employee_info')
   employment_info = db.relationship('EmploymentInfo', backref='employee_info')
   attendance_info = db.relationship('Attendance', backref='employee_info')
   leave_info = db.relationship('Leave', backref='employee_info')
   payslip_info = db.relationship('Payslips', backref='employee_info')

   @hybrid_property
   def fullname(self):
      return self.first_name + ' ' + self.middle_name + ' ' + self.last_name
   
   @hybrid_property
   def getEmployment(self):
      if self.employment_info:
         return self.employment_info
      else:
         return None

   @hybrid_property
   def getUserInfo(self):
      if self.user_info:
         return self.user_info
      else:
         return None

   @hybrid_property
   def getAttendanceInfo(self):
      if self.attendance_info:
         return self.attendance_info
      else:
         return None

   @hybrid_property
   def getLeaveInfo(self):
      if self.leave_info:
         return self.leave_info
      else:
         return None
      
class EmploymentInfo(db.Model):
   #Primary Key
   id = db.Column(db.Integer(), primary_key=True)

   description = db.Column(db.String(length=500))   
   
   start_date= db.Column(db.Date(), nullable=False)
   end_date = db.Column(db.Date(), nullable=True)
   status = db.Column(db.Enum(HIRE_TYPES), nullable=False, default=HIRE_TYPES.Hired)

   #Foreign Key
   employee_id = db.Column(db.Integer(), db.ForeignKey('employee_info.id', ondelete="CASCADE"))
   salary_id = db.Column(db.Integer(), db.ForeignKey('salaries.id'))

   @hybrid_property
   def is_active(self):
       """Return True if the EmploymentInfo is currently active, False otherwise."""
       return self.end_date is None or self.end_date > date.today()

class Salaries(db.Model):
   #Primary Key
   id = db.Column(db.Integer(), primary_key=True)

   salary_name = db.Column(db.String(length=50), nullable=False)
   description = db.Column(db.String(length=500))
   daily_rate = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   hourly_rate = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   bir_tax = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   sss_tax = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   phil_health_tax = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   pag_ibig_tax = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   ot_rate = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   allowance = db.Column(db.Float(precision=2, asdecimal=True), nullable=False) #non-taxable

   #Relationship Salary can have many Employment
   employment_info = db.relationship('EmploymentInfo', backref='salary')
  
class Payslips(db.Model):
   #Primary Key
   id = db.Column(db.Integer(), primary_key=True)
   name = db.Column(db.String(length=500), nullable=False)
   start_cut_off = db.Column(db.Date(), nullable=False)
   end_cut_off = db.Column(db.Date(), nullable=False)
   days_present = db.Column(db.Integer(), nullable=False)
   total_regular_hours = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   pre_ot_hours = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   post_ot_hours = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   total_ot_hours = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   gross_pay = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   deductions = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   allowance = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   net_pay = db.Column(db.Float(precision=2, asdecimal=True), nullable=False)
   status = db.Column(db.Enum(STATUS_TYPES), default=STATUS_TYPES.Pending, nullable=False)

   #Foreign Key
   employee_id = db.Column(db.Integer(), db.ForeignKey('employee_info.id', ondelete="CASCADE"))

class Attendance(db.Model):
   #Primary Key
   id = db.Column(db.Integer(), primary_key=True)

   #shift
   date= db.Column(db.Date(), nullable=False)
   attendance_type = db.Column(db.Enum(ATTENDANCE_TYPES), default=ATTENDANCE_TYPES.Unavailable, nullable=False)
   status = db.Column(db.Enum(STATUS_TYPES), default=STATUS_TYPES.Pending, nullable=False)
   start_shift= db.Column(db.Time(), nullable=False)
   end_shift= db.Column(db.Time(), nullable=False)

   # Time
   checked_in= db.Column(db.Time(),  nullable=True)
   checked_out= db.Column(db.Time(), nullable=True)

   #todo pre-post ot 
   pre_ot= db.Column(db.Time())
   post_ot= db.Column(db.Time())

   #Foreign Keys  
   employee_id = db.Column(db.Integer(), db.ForeignKey('employee_info.id', ondelete="CASCADE"))

   @hybrid_property
   def total_hours(self):
      if self.checked_out is not None and self.checked_in is not None:
         checked_out_value = getattr(self, 'checked_out')
         checked_in_value = getattr(self, 'checked_in')
         checked_out_time = checked_out_value
         checked_out_datetime = datetime.combine(datetime.min, checked_out_time)
         checked_in_time = checked_in_value
         checked_in_datetime = datetime.combine(datetime.min, checked_in_time)
         time_diff = checked_out_datetime - checked_in_datetime
         return round(time_diff.total_seconds() / 3600, 2)
      else:
         return None


   @hybrid_property
   def total_regular_hours(self):
      if self.pre_ot is not None or self.post_ot is not None:
         regular_hours = 0
         if self.checked_out is not None and self.checked_in is not None:
               checked_out_value = getattr(self, 'checked_out')
               checked_in_value = getattr(self, 'checked_in')
               checked_out_time = checked_out_value
               checked_out_datetime = datetime.combine(datetime.min, checked_out_time)
               checked_in_time = checked_in_value
               checked_in_datetime = datetime.combine(datetime.min, checked_in_time)
               time_diff = checked_out_datetime - checked_in_datetime
               total_hours = round(time_diff.total_seconds() / 3600, 2)

               if self.pre_ot is not None:
                  pre_ot_hours = (datetime.combine(datetime.min, self.pre_ot) - datetime.combine(datetime.min, self.start_shift)).total_seconds() / 3600.0
                  if total_hours > pre_ot_hours:
                     regular_hours += total_hours - pre_ot_hours

               if self.post_ot is not None:
                  post_ot_hours = (datetime.combine(datetime.min, self.post_ot) - datetime.combine(datetime.min, self.end_shift)).total_seconds() / 3600.0
                  if total_hours > post_ot_hours:
                     regular_hours += total_hours - post_ot_hours
               
               return regular_hours
      else:
         return self.total_hours
      
          
   @hybrid_property
   def pre_ot_hours(self):
      
      if self.pre_ot is not None and self.start_shift is not None:
         pre_ot_value = getattr(self, 'pre_ot')
         start_shift_value = getattr(self, 'start_shift')
         pre_ot_datetime = datetime.combine(datetime.min, pre_ot_value)
         start_shift_datetime = datetime.combine(datetime.min, start_shift_value)
         time_diff =  start_shift_datetime - pre_ot_datetime
         
         return round(time_diff.total_seconds() / 3600, 2)
      else:
         return None
      
   @hybrid_property
   def post_ot_hours(self):
      if self.post_ot is not None and self.end_shift is not None:
         post_ot_value = getattr(self, 'post_ot')
         end_shift_value = getattr(self, 'end_shift')
         post_ot_datetime = datetime.combine(datetime.min, post_ot_value)
         end_shift_datetime = datetime.combine(datetime.min, end_shift_value)
         time_diff = post_ot_datetime - end_shift_datetime
         
         return round(time_diff.total_seconds() / 3600, 2)
      else:
         return None
      

class Leave(db.Model):
   #Primary Key
   id = db.Column(db.Integer(), primary_key=True)

   type = db.Column(db.Enum(LEAVE_TYPES), default=LEAVE_TYPES.Sick_Leave, nullable=False)
   date_requested= db.Column(db.Date(), default=func.current_date(), nullable=False)
   leave_date= db.Column(db.Date(), nullable=False)
   status = db.Column(db.Enum(STATUS_TYPES),default=STATUS_TYPES.Pending, nullable=False)
   processed_date = db.Column(db.Date())
   processed_by = db.Column(db.String(length=50))

   #Foreign Keys  
   employee_id = db.Column(db.Integer(), db.ForeignKey('employee_info.id', ondelete="CASCADE"))

class Positions(db.Model):
   #Primary Key
   id = db.Column(db.Integer(), primary_key=True)

   position_name = db.Column(db.String(length=50), nullable=False)
   description = db.Column(db.String(length=500))
   position_status = db.Column(db.Enum(POSITION_STATUS), default=POSITION_STATUS.Hiring, nullable=False)
   date_created= db.Column(db.Date(), default=func.current_date(), nullable=False)

   #Foreign Key
   department_id = db.Column(db.Integer(), db.ForeignKey('departments.id', ondelete="CASCADE"))

   #Association Proxy
   dept_assigned = association_proxy('departments', 'department_name')

   def obj_to_dict(self):
      return {
         'id': self.id,
         'position_name': self.position_name,
         'department_id': self.department_id
      }

class Departments(db.Model):
   #Primary Key
   id = db.Column(db.Integer(), primary_key=True)

   department_name = db.Column(db.String(length=50), nullable=False)
   manager = db.Column(db.String(length=50))
   description = db.Column(db.String(length=500))
   date_created= db.Column(db.Date(), default=func.current_date(), nullable=False)

   #Relationship
   positions_info = db.relationship('Positions', backref='departments_info')

   def obj_to_dict(self):
      return {
         'id': self.id,
         'department_name': self.department_name,
      }
      
   @hybrid_property
   def getPositions(self):
      if self.positions_info:
         return self.positions_info
      else:
         return None
   


  