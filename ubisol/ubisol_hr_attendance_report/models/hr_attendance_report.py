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
    worked_hours = fields.Float(string='Worked Hours', compute="_compute_worked_hours", store=True, compute_sudo=True)

    difference_check_in = fields.Float(compute="_compute_difference_check_in", store=True, compute_sudo=True)
    difference_check_out = fields.Float(compute="_compute_difference_check_out", store=True, compute_sudo=True)


    @api.depends("check_in", "start_work")
    def _compute_difference_check_in(self):
        for record in self:
            if record.check_in:
                if record.start_work >= record.check_in:
                    record.difference_check_in = 0
                else:
                    record.difference_check_in = (
                        ((record.check_in).day*3600*24 + (record.check_in).hour*3600 + (record.check_in).minute*60 + (record.check_in).second)
                        - 
                        ((record.start_work).day*3600*24 + (record.start_work).hour*3600 + (record.start_work).minute*60 + (record.start_work).second) 
                        ) / 3600
            else:
                record.difference_check_in = 0

    @api.depends("check_out", "end_work")
    def _compute_difference_check_out(self):
        for record in self:
            if record.check_out:
                if record.check_out >= record.end_work:
                    record.difference_check_out = 0
                else:
                    record.difference_check_out = (
                        ((record.end_work).day*3600*24 + (record.end_work).hour*3600 + (record.end_work).minute*60 + (record.end_work).second)
                        -
                        ((record.check_out).day*3600*24 + (record.check_out).hour*3600 + (record.check_out).minute*60 + (record.check_out).second)
                        ) / 3600
            else:
                record.difference_check_out = 0

    @api.depends('check_in', "start_work", 'check_out', "end_work", "day_period")
    def _compute_worked_hours(self):
        setting_obj = self.env['res.config.settings'].search([], limit=1, order='id desc')
        for record in self:
            is_rest = True
            is_rest = record.day_period.is_rest
            if is_rest:
                record.worked_hours = 0.0
            else:
                check_in = record.start_work
                check_out = record.end_work
                if record.check_out and record.check_in:
                    if record.start_work < record.check_in:
                        if (setting_obj.late_min * 3600) < (record.check_in - record.start_work).total_seconds():
                            check_in = record.check_in
                    if record.check_out < record.end_work:
                        check_out = record.check_out
                    delta = check_out - check_in
                    record.worked_hours = delta.total_seconds() / 3600.0
                elif record.check_out:
                    if record.check_out < record.end_work:
                        check_out = record.check_out
                    delta = check_out - check_in
                    record.worked_hours = delta.total_seconds() / 3600.0 - setting_obj.late_subtrack
                    if record.worked_hours < 0.0:
                        record.worked_hours = 0.0
                elif record.check_in:
                    if record.start_work < record.check_in:
                        if (setting_obj.late_min * 3600) < (record.check_in - record.start_work).total_seconds():
                            check_in = record.check_in
                    delta = check_out - check_in
                    record.worked_hours = delta.total_seconds() / 3600.0 - setting_obj.late_subtrack
                    if record.worked_hours < 0.0:
                        record.worked_hours = 0.0
                else:
                    record.worked_hours = 0.0

    def _convert_datetime_field(self, datetime_field, user=None):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        date_result = pytz.utc.localize(datetime_field).astimezone(local)
        seconds = date_result.utcoffset().total_seconds()
        date_result = date_result - timedelta(hours=seconds/1800)
        return datetime.strftime(date_result, '%Y-%m-%d %H:%M:%S')

    def calculate_report(self, start_date, end_date):
        employees = []
        self._cr.execute('SELECT DISTINCT id AS hr_employee FROM hr_employee')
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

                        self.env['hr.attendance.report'].search([('hr_employee_schedule', '=', schedule.id)]).unlink()

                    date_from = datetime.combine(dates_btwn, time())
                    date_from = date_from + timedelta(hours=5) + timedelta(minutes=0) + timedelta(seconds=0)
                    date_to = datetime.combine(dates_btwn, time())
                    date_to = date_to + timedelta(hours=14) + timedelta(minutes=0) + timedelta(seconds=0)
                    # print("date_from: ", date_from, "date_to: ", date_to)
                    attendances = self.env['hr.attendance'].search([
                        ('check_in', '>=', self._convert_datetime_field(date_from)),
                        ('check_in', '<=', self._convert_datetime_field(date_to)),
                        ('employee_id', '=', employee['hr_employee']),
                    ])
                    if not attendances:
                        date_from = datetime.combine(dates_btwn, time())
                        date_from = date_from + timedelta(hours=14) + timedelta(minutes=0) + timedelta(seconds=1)
                        date_to = datetime.combine(dates_btwn, time())
                        date_to = date_to + timedelta(hours=28) + timedelta(minutes=59) + timedelta(seconds=59)
                        attendances = self.env['hr.attendance'].search([
                            ('check_out', '>=', self._convert_datetime_field(date_from)),
                            ('check_out', '<=', self._convert_datetime_field(date_to)),
                            ('employee_id', '=', employee['hr_employee']),
                        ])

                    for attendance in attendances:
                        if attendance:
                            values['hr_attendance'] = attendance.id
                            values['check_in'] = attendance.check_in
                            values['check_out'] = attendance.check_out
                            values['worked_hours'] = attendance.worked_hours

                            self.env['hr.attendance.report'].search([('hr_attendance', '=', attendance.id)]).unlink()
                        
                    super(HrAttendanceReport, self).create(values)
                dates_btwn = dates_btwn + relativedelta(days=1)