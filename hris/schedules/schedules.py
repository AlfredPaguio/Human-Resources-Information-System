from datetime import datetime, timedelta

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import login_required

from hris.models import *

from .forms import *

schedules_bp = Blueprint('schedules_bp', __name__,  template_folder='templates',
    static_folder='static', static_url_path='schedules/static')

@schedules_bp.route('schedules/get_attendance', methods=['GET'])
@login_required
def get_attendance():
    employee_id = request.args.get('employee_id')
    schedules = Attendance.query.filter_by(employee_id = employee_id).all()
    
    schedules = [{'id': schedule.id, 
                  'date': schedule.date.strftime("%y/%m/%d"), 
                  'attendance_type': schedule.attendance_type.value,
                  'status': schedule.status.value,
                  'start_shift': schedule.start_shift.isoformat(),
                  'end_shift': schedule.end_shift.isoformat(),
                  'checked_in': schedule.checked_in.isoformat() if schedule.checked_in is not None else None,
                  'checked_out': schedule.checked_out.isoformat() if schedule.checked_out is not None else None,
                  'employee_id':schedule.employee_id} for schedule in schedules]
    
    return jsonify(schedules)


@schedules_bp.route('/schedules/confirm_attendance/<int:employee_id>/<string:employee_name>', methods=['POST'])
@login_required
def confirm_attendance(employee_id, employee_name):
    if request.method == 'POST':
        schedule_id = request.form.get('schedule_id')   
        attendance = Attendance.query.filter_by(id = schedule_id).first()


        if attendance.attendance_type.value == 'Unavailable' and\
            attendance.checked_in != None and attendance.checked_out != None:
            attendance.attendance_type = 'Present'

        attendance.status = 'Approved'
        db.session.commit()

        flash('Attendance approved!', category='success')
        return redirect(url_for('schedules_bp.manage_schedule', employee_id=employee_id, employee_name=employee_name))

@schedules_bp.route('/schedules', methods=['GET', 'POST'])
@login_required
def schedules():
    employees = db.session.query(EmployeeInfo.id, EmployeeInfo.last_name, EmployeeInfo.first_name, 
    EmployeeInfo.middle_name, EmployeeInfo.fullname, Positions.position_name, Departments.department_name,
    EmploymentInfo.status)\
    .join(EmployeeInfo, EmployeeInfo.id == EmploymentInfo.employee_id)\
    .join(Positions, Positions.id == EmployeeInfo.position_id)\
    .join(Departments, Departments.id == Positions.department_id)\
    .filter(EmploymentInfo.status == 'Hired').all()

    return render_template('schedules.html', employees=employees)

@schedules_bp.route('/schedules/manage_schedule/<int:employee_id>/<string:employee_name>', methods=['GET', 'POST'])
@login_required
def manage_schedule(employee_id, employee_name):
    add_schedule_modal = AddScheduleModal()
    edit_schedule_modal = EditScheduleModal()
    if request.method == 'POST':
        if add_schedule_modal.validate_on_submit():

            start_date = datetime.strptime(add_schedule_modal.start_date.data, '%Y-%m-%d')
            end_date = datetime.strptime(add_schedule_modal.end_date.data, '%Y-%m-%d')

            dates_in_between = []
            current_date = start_date

            while current_date <= end_date:
                if current_date.weekday() not in [5,6]:
                    dates_in_between.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
               
            schedules_to_insert = []
            for date in dates_in_between:
                    schedules_to_insert.append({
                        'date' : date,
                        'start_shift' : add_schedule_modal.start_shift.data,
                        'end_shift' : add_schedule_modal.end_shift.data,
                        'employee_id' : employee_id
                    })
                
            db.session.bulk_insert_mappings(Attendance, schedules_to_insert)
            db.session.commit()
            
            flash('Schedule added!', category='success')
            return redirect(url_for('schedules_bp.manage_schedule', employee_id=employee_id, employee_name=employee_name))
        
    return render_template('manage_schedule.html', employee_id=employee_id, 
                                                add_schedule_modal=add_schedule_modal,
                                                employee_name=employee_name,
                                                edit_schedule_modal=edit_schedule_modal)


@schedules_bp.route('schedules/edit_schedule/<int:employee_id>/<string:employee_name>', methods=['POST'])
@login_required
def edit_schedule(employee_id, employee_name):
    edit_schedule_modal = EditScheduleModal(request.form)

    if request.method == 'POST':
        if edit_schedule_modal.validate_on_submit():
            updated_schedule = Attendance.query.filter_by(id = edit_schedule_modal.schedule_id.data).first()
            
            start_shift = datetime.strptime(edit_schedule_modal.start_shift.data, "%H:%M")
            end_shift = datetime.strptime(edit_schedule_modal.end_shift.data, "%H:%M")

            try:
                checked_in = datetime.strptime(edit_schedule_modal.checked_in.data, "%H:%M")
            except:
                checked_in = None

            try:
                checked_out = datetime.strptime(edit_schedule_modal.checked_out.data, "%H:%M")
            except:
                checked_out = None

            if start_shift > end_shift:
                flash('Starting shift must not exceed the ending shift!', category='danger')
            else:
                updated_schedule.start_shift = start_shift
                updated_schedule.end_shift = end_shift

                time_diff = checked_in - start_shift 

                if checked_in:
                    if time_diff > timedelta(minutes=15):
                        updated_schedule.attendance_type = 'Late'
                    else:
                        updated_schedule.attendance_type = 'Present'

                    if checked_in < start_shift:
                        updated_schedule.pre_ot = checked_in
                    else:
                        updated_schedule.pre_ot = None

                if checked_out:
                    if checked_out > end_shift:
                        updated_schedule.post_ot = checked_out
                    else:
                        updated_schedule.post_ot = None
                    
                updated_schedule.checked_in = checked_in
                updated_schedule.checked_out = checked_out

                db.session.commit()     
                flash(f'Schedule/Attendance for {updated_schedule.date} edited!', category='success')


        return redirect(url_for('schedules_bp.manage_schedule', employee_id=employee_id, employee_name=employee_name))


@schedules_bp.route('schedules/delete_schedule/<int:employee_id>/<string:employee_name>', methods=['POST'])
@login_required
def delete_schedule(employee_id, employee_name):
    if request.method == 'POST':
        delete_id = request.form.get('schedule_id')
        Attendance.query.filter_by(id = delete_id).delete()
        db.session.commit()
        flash(f'Schedule deleted!', category='danger')
        return redirect(url_for('schedules_bp.manage_schedule', employee_id=employee_id, employee_name=employee_name))


# Leave Requests
@schedules_bp.route('/schedules/leave_requests/<int:employee_id>/<string:employee_name>', methods=['GET', 'POST'])
@login_required
def get_leave_requests(employee_id, employee_name):
    leave_requests = Leave.query.filter_by(employee_id = employee_id).all()
    return render_template('leave_requests.html', leave_requests=leave_requests, employee_name=employee_name, employee_id=employee_id)


@schedules_bp.route('schedules/accept_leave_request/<int:employee_id>/<string:employee_name>', methods=['POST'])
@login_required
def accept_leave_request(employee_id, employee_name):
    if request.method == 'POST':
        leave_id = request.form.get('accept')

        leave = Leave.query.filter_by(id = leave_id).first()

        if leave:
            attendance = Attendance.query.filter_by(date=leave.leave_date, 
                                                    employee_id=employee_id).first()
            
            if attendance:
                if attendance.attendance_type.value is not 'Unavailable':
                    attendance.checked_out = datetime.now().strftime('%H:%M:%S')
                    attendance.status = 'Approved'

                    leave.status = 'Approved'
                    leave.processed_date = datetime.now().strftime('%Y-%m-%d')
                    leave.processed_by = current_user.name

                    db.session.commit()

                    flash(f'Leave request during work hours accepted for {leave.leave_date}', category='success')
                else:
                    attendance.checked_out = None
                    attendance.checked_out = None
                    attendance.attendance_type = 'On_Leave'
                    attendance.status = 'Approved'

                    leave.status = 'Approved'
                    leave.processed_date = datetime.now().strftime('%Y-%m-%d')
                    leave.processed_by = current_user.name

                    db.session.commit()
                    flash(f'Leave request during non-working hours accepted for {leave.leave_date}', category='success')
            else:   
                leave.status = 'Approved'
                leave.processed_date = datetime.now().strftime('%Y-%m-%d')
                leave.processed_by = current_user.name

                db.session.commit()

                flash(f'Leave request accepted for {leave.leave_date}', category='success')
            
        return redirect(url_for('schedules_bp.get_leave_requests', employee_id=employee_id, employee_name=employee_name)) 


@schedules_bp.route('schedules/reject_leave_request/<int:employee_id>/<string:employee_name>', methods=['POST'])
@login_required
def reject_leave_request(employee_id, employee_name):
    if request.method == 'POST':
        leave_id = request.form.get('reject')
        leave = Leave.query.filter_by(id = leave_id).first()

        if leave:
            attendance = Attendance.query.filter_by(date=leave.leave_date,
                                                    employee_id=employee_id).first()

            if attendance.attendance_type.value != 'On_Leave':
                leave.status = 'Declined'
                leave.processed_date = datetime.now().strftime('%Y-%m-%d')
                leave.processed_by = current_user.name
                flash(f'Test {id}', category='danger')
                db.session.commit()

                flash(f'Leave Request Rejected: {id}', category='danger')
            else:
                attendance.attendance_type = 'Unavailable'
                attendance.status = 'Pending'

                leave.status = 'Declined'
                leave.processed_date = datetime.now().strftime('%Y-%m-%d')
                leave.processed_by = current_user.name
                flash(f'Test {id}', category='danger')
                db.session.commit()
            
                flash(f'Leave Request Rejected: {id}', category='danger')

        return redirect(url_for('schedules_bp.get_leave_requests', employee_id=employee_id, employee_name=employee_name))


