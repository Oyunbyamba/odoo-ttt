# -*- coding: utf-8 -*-

import pytz
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, time

class HrAttendanceReport(models.Model):
    """Ирцийн тайлан гаргахад шаардлагатай өгөгдөл хадгалах хүснэгт"""
    _name = 'hr.attendance.report'
    _description = 'Hr Attendance Report'

    hr_department = fields.Many2one('hr.department', string="Department", help="Department")
    hr_employee = fields.Many2one('hr.employee', string="Employee", help="Employee")
    hr_employee_shift = fields.Many2one('hr.employee.shift', string="Employee Shift", help="Employee Shift")
    hr_employee_schedule = fields.Many2one('hr.employee.schedule', string="Employee Schedule", help="Employee Schedule")
    hr_attendance = fields.Many2one('hr.attendance', string="Employee Attendance", help="Employee Attendance")
    hr_employee_shift_template = fields.Many2one('resource.calendar', 'Employee Shift Template')
    hr_employee_shift_dayplan = fields.Many2one('resource.calendar.shift', 'Employee Shift Plan of Day')
    date_from = fields.Date(string='Starting Date')
    date_to = fields.Date(string='End Date')
    work_day = fields.Date(string='End Date')
    shift_type = fields.Selection([
        ('days', 'Days'),
        ('shift', 'Shift')
    ], default="shift", tracking=True)
    week_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', required=True, index=True, default='0')
    day_period = fields.Many2one('resource.calendar.dayperiod', string="Day Period", help="Day Period of Work")
    day_period_int = fields.Integer(string='Day Period Integer', help='Day Period of Work')
    lunch_time_from = fields.Datetime(string='Lunch time from', required=True)
    lunch_time_to = fields.Datetime(string='Lunch time to', required=True)
    start_work = fields.Datetime(string="Start Work", required=True, help="Start Work")
    end_work = fields.Datetime(string="End Work", required=True, help="End Work")

    check_in = fields.Datetime(string="Check In")
    check_out = fields.Datetime(string="Check Out")
    worked_hours = fields.Float(string='Worked Hours')


    def _convert_datetime_field(self, datetime_field, user=None):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        date_result = pytz.utc.localize(datetime_field).astimezone(local)
        seconds = date_result.utcoffset().total_seconds()
        date_result = date_result - timedelta(hours=seconds/1800)
        return datetime.strftime(date_result, '%Y-%m-%d %H:%M:%S')

    def calculate_report(self, start_date, end_date):
        employees = []
        self._cr.execute('SELECT DISTINCT hr_employee FROM hr_employee_schedule')
        for t in self._cr.dictfetchall():
            employees.append(t)
        for employee in employees:
            dates_btwn = start_date
            while dates_btwn <= end_date:
                schedules = self.env['hr.employee.schedule'].search([
                    ('work_day', '=', dates_btwn),
                    ('hr_employee', '=', employee['hr_employee']),
                ])
                for schedule in schedules:
                    if schedule:
                        values = {}
                        values['hr_department'] = schedule.hr_department.id
                        values['hr_employee'] = schedule.hr_employee.id
                        values['hr_employee_shift'] = schedule.hr_employee_shift.id
                        values['hr_employee_schedule'] = schedule.id
                        values['hr_employee_shift_template'] = schedule.hr_employee_shift_template.id
                        values['hr_employee_shift_dayplan'] = schedule.hr_employee_shift_dayplan.id
                        values['date_from'] = schedule.date_from
                        values['date_to'] = schedule.date_to
                        values['work_day'] = schedule.work_day
                        values['shift_type'] = schedule.shift_type
                        values['week_day'] = schedule.week_day
                        values['day_period'] = schedule.day_period.id
                        values['day_period_int'] = schedule.day_period_int
                        values['lunch_time_from'] = schedule.lunch_time_from
                        values['lunch_time_to'] = schedule.lunch_time_to
                        values['start_work'] = schedule.start_work
                        values['end_work'] = schedule.end_work

                    date_from = datetime.combine(dates_btwn, time())
                    date_to = datetime.combine(dates_btwn, time())
                    date_to = date_to + timedelta(hours=23) + timedelta(minutes=59) + timedelta(seconds=59)
                    attendances = self.env['hr.attendance'].search([
                        ('check_in', '>=', self._convert_datetime_field(date_from)),
                        ('check_in', '<=', self._convert_datetime_field(date_to)),
                        ('employee_id', '=', employee['hr_employee']),
                    ])
                    for attendance in attendances:
                        if attendance:
                            values['hr_attendance'] = attendance.id
                            values['check_in'] = attendance.check_in
                            values['check_out'] = attendance.check_out
                            values['worked_hours'] = attendance.worked_hours
                        
                    dates_btwn = dates_btwn + relativedelta(days=1)
                    super(HrAttendanceReport, self).create(values)
                