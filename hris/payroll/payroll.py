import calendar
from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, func, or_

from hris.models import *

from .forms import *

payroll_bp = Blueprint(
    "payroll_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="static",
)


def calculate_payroll(
    selected_employee,
    start_cut_off,
    end_cut_off,
    total_regular_hours=0,
    total_pre_ot_hours=0,
    total_post_ot_hours=0,
    allowance=0,
):
    employee_attendances = (
        Attendance.query.filter(Attendance.employee_id == selected_employee.id)
        .filter(
            Attendance.date.between(
                datetime.strptime(start_cut_off, "%Y-%m-%d"),
                datetime.strptime(end_cut_off, "%Y-%m-%d"),
            )
        )
        .filter(
            or_(
                Attendance.attendance_type == "Present",
                Attendance.attendance_type == "Late",
            )
        )
        .filter(Attendance.status == STATUS_TYPES.Approved)
    )

    if total_regular_hours == 0:
        for res in employee_attendances:
            if res.total_regular_hours > 5.0:
                g = res.total_regular_hours - 1.0
                total_regular_hours += g
            else:
                g = res.total_regular_hours
                total_regular_hours += g

    if total_pre_ot_hours == 0:
        for res in employee_attendances:
            if res.pre_ot_hours is not None:
                g = res.pre_ot_hours
                total_pre_ot_hours += g

    if total_post_ot_hours == 0:
        for res in employee_attendances:
            if res.post_ot_hours is not None:
                g = res.post_ot_hours
                total_post_ot_hours += g

    # Calculate days present
    days_present = employee_attendances.with_entities(
        func.count(Attendance.id)
    ).scalar()

    # Calculate ot hours
    total_ot_hours = total_pre_ot_hours + total_post_ot_hours

    # Calculate gross pay
    gross_pay = (float(total_regular_hours) * float(selected_employee.hourly_rate)) + (
        float(total_ot_hours) * float(selected_employee.ot_rate)
    )

    # Calculate deductions
    deductions = (
        float(selected_employee.bir_tax)
        + float(selected_employee.sss_tax)
        + float(selected_employee.phil_health_tax)
        + float(selected_employee.pag_ibig_tax)
    )

    # Calculate net pay
    net_pay = (gross_pay - deductions) + float(selected_employee.allowance)

    data = {
        "employee_id": selected_employee.id,
        "employee_name": selected_employee.fullname,
        "image_path": selected_employee.image_path,
        "company_email": selected_employee.company_email,
        "mobile": selected_employee.mobile,
        "bir_tax": float(selected_employee.bir_tax),
        "sss_tax": float(selected_employee.sss_tax),
        "phil_health_tax": float(selected_employee.phil_health_tax),
        "pag_ibig_tax": float(selected_employee.pag_ibig_tax),
        "hourly_rate": float(selected_employee.hourly_rate),
        "ot_rate": float(selected_employee.ot_rate),
        "start_cut_off": start_cut_off,
        "end_cut_off": end_cut_off,
        "days_present": int(days_present),
        "total_regular_hours": total_regular_hours,
        "pre_ot_hours": total_pre_ot_hours,
        "post_ot_hours": total_post_ot_hours,
        "total_ot_hours": total_ot_hours,
        "gross_pay": gross_pay,
        "deductions": deductions,
        "allowance": allowance,
        "net_pay": net_pay,
    }

    return data


def get_payroll(start_cut_off, end_cut_off):
    employees = (
        db.session.query(
            Users.image_path,
            Users.company_email,
            EmployeeInfo.id,
            EmployeeInfo.fullname,
            EmployeeInfo.mobile,
            EmploymentInfo.status,
            Salaries.daily_rate,
            Salaries.hourly_rate,
            Salaries.bir_tax,
            Salaries.sss_tax,
            Salaries.phil_health_tax,
            Salaries.pag_ibig_tax,
            Salaries.ot_rate,
            Salaries.allowance,
        )
        .join(EmployeeInfo, EmployeeInfo.id == EmploymentInfo.employee_id)
        .join(Users, Users.employee_id == EmployeeInfo.id)
        .join(Salaries, Salaries.id == EmploymentInfo.salary_id)
        .all()
    )

    employee_data = []
    for employee in employees:
        employee_payslip = (
            db.session.query(Payslips)
            .filter(Payslips.employee_id == employee.id)
            .filter(Payslips.start_cut_off == start_cut_off)
            .filter(Payslips.end_cut_off == end_cut_off)
            .first()
        )

        # Calculate Payroll
        data = calculate_payroll(
            employee,
            start_cut_off,
            end_cut_off,
            total_regular_hours=(
                float(employee_payslip.total_regular_hours)
                if employee_payslip is not None
                else 0
            ),
            total_pre_ot_hours=(
                float(employee_payslip.pre_ot_hours)
                if employee_payslip is not None
                else 0
            ),
            total_post_ot_hours=(
                float(employee_payslip.post_ot_hours)
                if employee_payslip is not None
                else 0
            ),
            allowance=(
                float(employee_payslip.allowance)
                if employee_payslip is not None
                else employee.allowance
            ),
        )

        if employee_payslip is None:

            new_payslip = Payslips(
                name=employee.fullname,
                start_cut_off=start_cut_off,
                end_cut_off=end_cut_off,
                days_present=data["days_present"],
                total_regular_hours=data["total_regular_hours"],
                pre_ot_hours=data["pre_ot_hours"],
                post_ot_hours=data["post_ot_hours"],
                total_ot_hours=data["total_ot_hours"],
                gross_pay=data["gross_pay"],
                deductions=data["deductions"],
                allowance=data["allowance"],
                net_pay=data["net_pay"],
                status="Pending",
                employee_id=employee.id,
            )

            db.session.add(new_payslip)
            db.session.commit()

        else:
            # Updates every click when total days is less than 10
            if data["days_present"] < 10:
                employee_payslip.days_present = data["days_present"]
                employee_payslip.total_regular_hours = data["total_regular_hours"]
                employee_payslip.pre_ot_hours = data["pre_ot_hours"]
                employee_payslip.post_ot_hours = data["post_ot_hours"]
                employee_payslip.total_ot_hours = data["total_ot_hours"]
                employee_payslip.gross_pay = data["gross_pay"]
                employee_payslip.deductions = data["deductions"]
                employee_payslip.allowance = data["allowance"]
                employee_payslip.net_pay = data["net_pay"]

                db.session.commit()

            data["status"] = employee_payslip.status.value
            employee_data.append(data)

    return employee_data


def get_cut_off(selected_month=None):
    today = datetime.now()

    if selected_month is None:
        this_month = today.month
    else:
        this_month = selected_month

    first_day_of_month = datetime(today.year, this_month, 1).date()
    last_day_of_month = datetime(
        today.year, this_month, calendar.monthrange(today.year, this_month)[1]
    ).date()

    first_cut_off = [str(first_day_of_month), None]
    second_cut_off = [None, str(last_day_of_month)]

    num_days_in_month = calendar.monthrange(today.year, this_month)[1]

    for day in range(1, num_days_in_month + 1):
        if day == 15:
            first_cut_off[1] = str(datetime(today.year, this_month, day).date())
        elif day == 16:
            second_cut_off[0] = str(datetime(today.year, this_month, day).date())

    return {
        "month": calendar.month_name[selected_month],
        "first_cut_off": first_cut_off,
        "second_cut_off": second_cut_off,
    }


@payroll_bp.route("/payroll", methods=["GET"])
@login_required
def payroll():
    current_month = datetime.now().month

    yearly_cutoff = []
    for month in range(1, current_month + 1):
        yearly_cutoff.append(get_cut_off(month))

    return render_template("payroll.html", yearly_cutoff=yearly_cutoff)


@payroll_bp.route(
    "/payroll/cut_off/<string:start_cut_off>/<string:end_cut_off>",
    methods=["GET", "POST"],
)
@login_required
def cut_off(start_cut_off, end_cut_off):
    refresh_form = RefreshPayrollForm()
    employee_data = get_payroll(start_cut_off, end_cut_off)

    if request.method == "POST":
        if request.args.get("req") == "refresh":
            db.session.query(Payslips).filter(
                Payslips.start_cut_off == start_cut_off
            ).filter(Payslips.end_cut_off == end_cut_off).delete()

            db.session.commit()
            flash("Payroll has been refreshed", category="success")
            return redirect(
                url_for(
                    "payroll_bp.cut_off",
                    start_cut_off=start_cut_off,
                    end_cut_off=end_cut_off,
                )
            )

    return render_template(
        "cut_off.html",
        employee_data=employee_data,
        start_cut_off=start_cut_off,
        end_cut_off=end_cut_off,
        refresh_form=refresh_form,
    )


@payroll_bp.route(
    "/payroll/cut_off/<int:employee_id>/<string:start_cut_off>/<string:end_cut_off>",
    methods=["GET", "POST"],
)
@login_required
def individual_payroll(employee_id, start_cut_off, end_cut_off):
    decline_payslip = DeclinePayslipForm()
    approve_payslip = ApprovePayslipForm()
    cancel_payslip = CancelPayslipForm()
    edit_payslip = EditPayslipForm()

    if session.get("payroll_data") is None:
        session["payroll_data"] = None

    selected_employee = (
        db.session.query(
            Users.image_path,
            Users.company_email,
            EmployeeInfo.id,
            EmployeeInfo.fullname,
            EmployeeInfo.mobile,
            EmploymentInfo.status,
            Salaries.daily_rate,
            Salaries.hourly_rate,
            Salaries.bir_tax,
            Salaries.sss_tax,
            Salaries.phil_health_tax,
            Salaries.pag_ibig_tax,
            Salaries.ot_rate,
            Salaries.allowance,
        )
        .filter(EmployeeInfo.id == employee_id)
        .join(EmployeeInfo, EmployeeInfo.id == EmploymentInfo.employee_id)
        .join(Users, Users.employee_id == EmployeeInfo.id)
        .join(Salaries, Salaries.id == EmploymentInfo.salary_id)
        .first()
    )

    employee_payslip = (
        db.session.query(Payslips)
        .filter(Payslips.employee_id == selected_employee.id)
        .filter(Payslips.start_cut_off == start_cut_off)
        .filter(Payslips.end_cut_off == end_cut_off)
        .first()
    )

    data = calculate_payroll(
        selected_employee,
        start_cut_off,
        end_cut_off,
        total_regular_hours=float(employee_payslip.total_regular_hours),
        total_pre_ot_hours=float(employee_payslip.pre_ot_hours),
        total_post_ot_hours=float(employee_payslip.post_ot_hours),
        allowance=float(employee_payslip.allowance),
    )

    # Temp key:value
    data["status"] = employee_payslip.status.value

    edit_payslip.total_regular_hours.data = data["total_regular_hours"]
    edit_payslip.pre_ot_hours.data = data["pre_ot_hours"]
    edit_payslip.post_ot_hours.data = data["post_ot_hours"]
    edit_payslip.allowance.data = data["allowance"]

    if request.method == "POST":
        if request.args.get("req") == "edit":
            edit_payslip = EditPayslipForm(request.form)

            if edit_payslip.validate_on_submit:

                employee_payslip.total_regular_hours = (
                    edit_payslip.total_regular_hours.data
                )
                employee_payslip.pre_ot_hours = edit_payslip.pre_ot_hours.data
                employee_payslip.post_ot_hours = edit_payslip.post_ot_hours.data
                employee_payslip.allowance = edit_payslip.allowance.data

                db.session.commit()

                flash("Edit Success", category="warning")

                return redirect(
                    url_for(
                        "payroll_bp.individual_payroll",
                        employee_id=employee_id,
                        start_cut_off=start_cut_off,
                        end_cut_off=end_cut_off,
                    )
                )

        if request.args.get("req") == "approve":
            approve_payslip = ApprovePayslipForm(request.form)
            if approve_payslip.validate_on_submit:

                employee_payslip.gross_pay = data["gross_pay"]
                employee_payslip.net_pay = data["net_pay"]
                employee_payslip.status = "Approved"

                data["status"] = employee_payslip.status
                db.session.commit()

                flash("Payroll Approved!", category="success")
                return redirect(
                    url_for(
                        "payroll_bp.cut_off",
                        employee_id=employee_id,
                        start_cut_off=start_cut_off,
                        end_cut_off=end_cut_off,
                    )
                )

        if request.args.get("req") == "decline":
            decline_payslip = DeclinePayslipForm(request.form)
            if decline_payslip.validate_on_submit:

                employee_payslip.status = "Declined"

                db.session.flush()

                data["status"] = employee_payslip.status
                db.session.commit()

                flash("Payroll Declined!", category="danger")
                return redirect(
                    url_for(
                        "payroll_bp.cut_off",
                        employee_id=employee_id,
                        start_cut_off=start_cut_off,
                        end_cut_off=end_cut_off,
                    )
                )

        if request.args.get("req") == "cancel":
            cancel_payslip = CancelPayslipForm(request.form)
            if cancel_payslip.validate_on_submit:

                employee_payslip.status = "Pending"

                db.session.flush()

                data["status"] = employee_payslip.status
                db.session.commit()

                flash("Payroll Canceled!", category="info")

                return redirect(
                    url_for(
                        "payroll_bp.cut_off",
                        employee_id=employee_id,
                        start_cut_off=start_cut_off,
                        end_cut_off=end_cut_off,
                    )
                )

    if request.method == "GET":

        return render_template(
            "individual_payroll.html",
            data=data,
            decline_payslip=decline_payslip,
            approve_payslip=approve_payslip,
            edit_payslip=edit_payslip,
            cancel_payslip=cancel_payslip,
        )
