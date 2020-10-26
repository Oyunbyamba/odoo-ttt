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
    work_hours = fields.Float(string='Must Worked Hours', compute="_compute_work_hours", store=True, compute_sudo=True)
    worked_hours = fields.Float(string='Worked Hours', compute="_compute_worked_hours", store=True, compute_sudo=True)

    difference_check_in = fields.Float(compute="_compute_difference_check_in", store=True, compute_sudo=True)
    difference_check_out = fields.Float(compute="_compute_difference_check_out", store=True, compute_sudo=True)

    overtime_req_id = fields.Many2one('hr.attendance.request')
    outside_work_req_id = fields.Many2one('hr.attendance.request')
    overtime = fields.Float(compute="_compute_overtime", store=True, compute_sudo=True)
    informal_overtime = fields.Float(compute="_compute_informal_overtime", store=True, compute_sudo=True)
    outside_work = fields.Float(compute="_compute_outside_work", store=True, compute_sudo=True)

    leave_id = fields.Many2one('hr.leave')
    leave_hours = fields.Float(compute="_compute_leave", store=True, compute_sudo=True)

    @api.depends("leave_id")
    def _compute_leave(self):
        for record in self:
            if record.leave_id:
                date_from = record.leave_id.date_from
                date_to = record.leave_id.date_to
                record.overtime = self._diff_by_hours(date_from, date_to)

    @api.depends("overtime_req_id")
    def _compute_overtime(self):
        for record in self:
            if record.overtime_req_id and (record.overtime_req_id.state == 'validate' or record.overtime_req_id.state == 'validate1'):
                check_out = record.check_out
                start_datetime = record.overtime_req_id.start_datetime
                if record.check_out:
                    if record.overtime_req_id.end_datetime < record.check_out:
                        check_out = record.overtime_req_id.end_datetime
                    record.overtime = self._diff_by_hours(check_out, start_datetime)
    
    @api.depends("outside_work_req_id")
    def _compute_outside_work(self):
        for record in self:
            if record.outside_work_req_id and (record.overtime_req_id.state == 'validate' or record.overtime_req_id.state == 'validate1'):
                check_out = record.check_out
                start_datetime = record.outside_work_req_id.start_datetime
                if not record.check_out or record.outside_work_req_id.end_datetime < record.check_out:
                    check_out = record.outside_work_req_id.end_datetime
                record.outside_work = self._diff_by_hours(check_out, start_datetime)

    @api.depends("check_in", "start_work")
    def _compute_difference_check_in(self):
        for record in self:
            if record.check_in:
                if record.start_work >= record.check_in:
                    record.difference_check_in = 0
                else:
                    record.difference_check_in = self._diff_by_hours(record.start_work, record.check_in)
            else:
                record.difference_check_in = 0

    @api.depends("check_out", "end_work")
    def _compute_difference_check_out(self):
        for record in self:
            if record.check_out:
                if record.check_out >= record.end_work:
                    record.difference_check_out = 0
                else:
                    record.difference_check_out = self._diff_by_hours(record.check_out, record.end_work)
            else:
                record.difference_check_out = 0

    @api.depends("start_work", "end_work")
    def _compute_work_hours(self):
        for record in self:
            is_rest = True
            is_rest = record.day_period.is_rest
            diff = record.lunch_time_to - record.lunch_time_from
            diff = diff.total_seconds() / 3600.0
            if is_rest:
                record.work_hours = 0.0
            else:
                record.work_hours = (record.end_work - record.start_work).total_seconds() / 3600 - diff
                if record.work_hours < 0.0:
                    record.work_hours = 0.0

    @api.depends('check_in', "start_work", 'check_out', "end_work", "day_period")
    def _compute_worked_hours(self):
        setting_obj = self.env['res.config.settings'].search([], limit=1, order='id desc')
        for record in self:
            is_rest = True
            is_rest = record.day_period.is_rest
            diff = record.lunch_time_to - record.lunch_time_from
            diff = diff.total_seconds() / 3600.0
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
                    record.worked_hours = delta.total_seconds() / 3600.0 - diff
                elif record.check_out:
                    if record.check_out < record.end_work:
                        check_out = record.check_out
                    delta = check_out - check_in
                    record.worked_hours = delta.total_seconds() / 3600.0 - setting_obj.late_subtrack - diff
                elif record.check_in:
                    if record.start_work < record.check_in:
                        if (setting_obj.late_min * 3600) < (record.check_in - record.start_work).total_seconds():
                            check_in = record.check_in
                    delta = check_out - check_in
                    record.worked_hours = delta.total_seconds() / 3600.0 - setting_obj.late_subtrack - diff
                else:
                    record.worked_hours = 0.0
            if record.worked_hours < 0.0:
                record.worked_hours = 0.0

    @api.depends('check_out', "end_work")
    def _compute_informal_overtime(self):
        for record in self:
            if not record.check_out:
                record.informal_overtime = 0.0
            elif record.check_out < record.end_work:
                record.informal_overtime = 0.0
            else:
                delta = record.check_out - record.end_work
                record.informal_overtime = delta.total_seconds() / 3600.0

    def _diff_by_hours(self, date1, date2):
        date = (
            ((date2).day*3600*24 + (date2).hour*3600 + (date2).minute*60 + (date2).second)
            -
            ((date1).day*3600*24 + (date1).hour*3600 + (date1).minute*60 + (date1).second)
            ) / 3600
        return date

    def _convert_datetime_field(self, datetime_field, user=None):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        date_result = pytz.utc.localize(datetime_field).astimezone(local)
        seconds = date_result.utcoffset().total_seconds()
        date_result = date_result - timedelta(hours=seconds/1800)
        return datetime.strftime(date_result, '%Y-%m-%d %H:%M:%S')

    def _get_departments(self, department, res):
        if department.child_ids:
            for child in department.child_ids:
                res.append(child.id)
                self._get_departments(child, res)
        return res

    def calculate_report(self, start_date, end_date, calculate_type, department_id, employee_id):
        setting_obj = self.env['res.config.settings'].search([], limit=1, order='id desc')
        employees = []
        if calculate_type == 'employee':
            for emp_id in employee_id:
                employees.append(emp_id.id)
        else:
            # get all child departments
            departments = self._get_departments(department_id, [])
            # get parent departments
            parents = department_id.ids[:]
            # combine departments
            departments = departments + parents
            # remove duplicates
            departments = list(dict.fromkeys(departments))
            if departments:
                for dep_id in departments:
                    self._cr.execute('SELECT DISTINCT id AS hr_employee FROM hr_employee WHERE department_id = ' + str(dep_id))
                    for t in self._cr.dictfetchall():
                        employees.append(t['hr_employee'])
            else:
                for dep_id in department_id:
                    self._cr.execute('SELECT DISTINCT id AS hr_employee FROM hr_employee WHERE department_id = ' + str(dep_id.id))
                    for t in self._cr.dictfetchall():
                        employees.append(t['hr_employee'])
        for employee_id in employees:
            dates_btwn = start_date
            while dates_btwn <= end_date:
                schedules = self.env['hr.employee.schedule'].search([
                    ('work_day', '=', dates_btwn),
                    ('hr_employee', '=', employee_id),
                ])
                emp = self.env['hr.employee'].browse(employee_id)
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

                    if values['shift_type'] == 'shift':
                        date_from = datetime.combine(dates_btwn, time())
                        date_to = datetime.combine(dates_btwn, time())
                        date_to = date_to + timedelta(hours=23, minutes=59, seconds=59)
                        attendances = self.env['hr.attendance'].search([
                            ('check_in', '>=', self._convert_datetime_field(date_from)),
                            ('check_in', '<=', self._convert_datetime_field(date_to)),
                            ('employee_id', '=', employee_id),
                        ])
                    else:
                        date_from = datetime.combine(dates_btwn, time())
                        date_from = date_from + timedelta(seconds=setting_obj.start_work_date_from * 3600)
                        date_to = datetime.combine(dates_btwn, time())
                        date_to = date_to + timedelta(seconds=setting_obj.start_work_date_to * 3600 + 59)
                        attendances = self.env['hr.attendance'].search([
                            ('check_in', '>=', self._convert_datetime_field(date_from)),
                            ('check_in', '<=', self._convert_datetime_field(date_to)),
                            ('employee_id', '=', employee_id),
                        ])
                        if not attendances:
                            date_from = datetime.combine(dates_btwn, time())
                            date_from = date_from + timedelta(seconds=setting_obj.end_work_date_from * 3600)
                            date_to = datetime.combine(dates_btwn, time())
                            date_to = date_to + timedelta(days=1) + timedelta(seconds=setting_obj.end_work_date_to * 3600 + 59)
                            attendances = self.env['hr.attendance'].search([
                                ('check_out', '>=', self._convert_datetime_field(date_from)),
                                ('check_out', '<=', self._convert_datetime_field(date_to)),
                                ('employee_id', '=', employee_id),
                            ])

                    for attendance in attendances:
                        if attendance:
                            values['hr_attendance'] = attendance.id
                            values['check_in'] = attendance.check_in
                            values['check_out'] = attendance.check_out
                            values['worked_hours'] = attendance.worked_hours

                            self.env['hr.attendance.report'].search([('hr_attendance', '=', attendance.id)]).unlink()

                    date_from = datetime.combine(dates_btwn, time())
                    date_to = datetime.combine(dates_btwn, time())
                    date_to = date_to + timedelta(hours=23, minutes=59, seconds=59)

                    attendance_reqs = self.env['hr.attendance.request'].search([
                        ('start_datetime', '>=', self._convert_datetime_field(date_from)),
                        ('start_datetime', '<=', self._convert_datetime_field(date_to)),
                        ('department_id', '=', emp.department_id.id),
                        ('request_type', '=', 'department'),
                    ])

                    for attendance_req in attendance_reqs:
                        if attendance_req.request_status_type == 'overtime':
                            values['overtime_req_id'] = attendance_req.id
                        elif attendance_req.request_status_type == 'outside_work':
                            values['outside_work_req_id'] = attendance_req.id

                    attendance_reqs = self.env['hr.attendance.request'].search([
                        ('start_datetime', '>=', self._convert_datetime_field(date_from)),
                        ('start_datetime', '<=', self._convert_datetime_field(date_to)),
                        ('employee_id', '=', employee_id),
                        ('request_type', '=', 'employee'),
                    ])

                    for attendance_req in attendance_reqs:
                        if attendance_req.request_status_type == 'overtime':
                            values['overtime_req_id'] = attendance_req.id
                        elif attendance_req.request_status_type == 'outside_work':
                            values['outside_work_req_id'] = attendance_req.id

                    leaves = self.env['hr.leave'].search([
                        ('date_from', '>=', self._convert_datetime_field(date_from)),
                        ('date_to', '<=', self._convert_datetime_field(date_to)),
                        ('employee_id', '=', employee_id),
                    ])

                    for leave in leaves:
                        if leave:
                            values['leave_id'] = leave.id

                    super(HrAttendanceReport, self).create(values)
                dates_btwn = dates_btwn + relativedelta(days=1)