from collections import Counter
from datetime import datetime, timedelta

import holidays
from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import or_

from hris.models import Attendance, Announcements, ATTENDANCE_TYPES

home_bp = Blueprint(
    "home_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/home/static",
)


@home_bp.route("/", methods=["GET", "POST"])
@home_bp.route("/home", methods=["GET", "POST"])
@login_required
def home():
    today = datetime.now().date()
    this_week = today.isocalendar()[1]

    attendances = (
        Attendance.query.filter(Attendance.date == today)
        .filter(
            or_(
                Attendance.attendance_type == ATTENDANCE_TYPES.Absent,
                Attendance.attendance_type == ATTENDANCE_TYPES.Present,
                Attendance.attendance_type == ATTENDANCE_TYPES.Late,
                Attendance.attendance_type == ATTENDANCE_TYPES.On_Leave,
            )
        )
        .all()
    )

    attendance_counts = Counter(
        [attendance.attendance_type for attendance in attendances]
    )

    statistics = [
        attendance_counts[ATTENDANCE_TYPES.Present],
        attendance_counts[ATTENDANCE_TYPES.Absent],
        attendance_counts[ATTENDANCE_TYPES.Late],
        attendance_counts[ATTENDANCE_TYPES.On_Leave],
    ]

    # Get the announcements for this month
    today = datetime.today().date()
    start_of_week = today - timedelta(days=today.weekday())
    # Calculate the start and end dates of the month
    start_of_month = today.replace(day=1)
    next_month = start_of_month.replace(month=start_of_month.month + 1, day=1)
    end_of_month = next_month - timedelta(days=1)

    announcements = Announcements.query.filter(
        or_(
            Announcements.date_created == today,
            Announcements.date_created >= start_of_week,
            Announcements.date_created >= start_of_month,
            Announcements.date_created <= end_of_month,
        )
    ).all()

    today_announcements = [
        announcement
        for announcement in announcements
        if announcement.date_created == today
    ]
    this_week_announcements = [
        announcement
        for announcement in announcements
        if announcement.date_created >= start_of_week
        and announcement.date_created <= today
    ]
    this_month_announcements = [
        announcement
        for announcement in announcements
        if announcement.date_created >= start_of_month
        and announcement.date_created <= today
    ]

    test = holidays.CountryHoliday("PH", years=[datetime.now().year])

    current_month = datetime.now().month

    # Events this month
    events_this_month = [
        (date.isoformat(), name)
        for date, name in test.items()
        if date.month == current_month
    ]

    # Events next month
    events_next_month = [
        (date.isoformat(), name)
        for date, name in test.items()
        if date.month == current_month + 1
    ]

    return render_template(
        "home.html",
        statistics=statistics,
        today_announcements=today_announcements,
        this_week_announcements=this_week_announcements,
        this_month_announcements=this_month_announcements,
        events_this_month=events_this_month,
        events_next_month=events_next_month,
    )
