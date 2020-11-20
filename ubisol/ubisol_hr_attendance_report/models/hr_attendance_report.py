# -*- coding: utf-8 -*-

import pytz
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, time
import xlsxwriter
import io
import xlwt,  base64

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
        ('days', '7 хоногоор'),
        ('shift', 'Ээлжээр')
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
    work_days = fields.Float(string='Must Worked Days', compute="_compute_work_days", store=True, compute_sudo=True)
    work_hours = fields.Float(string='Must Worked Hours', compute="_compute_work_hours", store=True, compute_sudo=True)
    worked_days = fields.Float(string='Worked Days', compute="_compute_worked_days", store=True, compute_sudo=True)
    worked_hours = fields.Float(string='Worked Hours', compute="_compute_worked_hours", store=True, compute_sudo=True)

    difference_check_in = fields.Float(compute="_compute_difference_check_in", store=True, compute_sudo=True)
    difference_check_out = fields.Float(compute="_compute_difference_check_out", store=True, compute_sudo=True)
    take_off_day = fields.Integer(compute="_compute_take_off_day", store=True, compute_sudo=True)

    paid_req_id = fields.Many2one('hr.leave')
    unpaid_req_id = fields.Many2one('hr.leave')
    vacation_req_id = fields.Many2one('hr.leave')
    overtime_req_id = fields.Many2one('hr.leave')
    outside_work_req_id = fields.Many2one('hr.leave')
    attendance_req_id = fields.Many2one('hr.leave')

    paid_req_time = fields.Float(compute="_compute_paid_req_time", store=True, compute_sudo=True)
    unpaid_req_time = fields.Float(compute="_compute_unpaid_req_time", store=True, compute_sudo=True)
    vacation_req_time = fields.Float(compute="_compute_vacation_req_time", store=True, compute_sudo=True)
    overtime = fields.Float(compute="_compute_overtime", store=True, compute_sudo=True)
    informal_overtime = fields.Float(compute="_compute_informal_overtime", store=True, compute_sudo=True)
    outside_work = fields.Float(compute="_compute_outside_work", store=True, compute_sudo=True)
    attendance_req_time = fields.Float(compute="_compute_attendance_req", store=True, compute_sudo=True)

    check_in_time = fields.Char(compute="_compute_check_in_time", compute_sudo=True)
    check_out_time = fields.Char(compute="_compute_check_out_time", compute_sudo=True)
    start_work_time = fields.Float(compute="_compute_start_work_time", compute_sudo=True)
    end_work_time = fields.Float(compute="_compute_end_work_time", compute_sudo=True)

    full_name = fields.Char(compute="_compute_full_name", store=True, compute_sudo=True)

    @api.depends("hr_employee")
    def _compute_full_name(self):
        for record in self:
            employee = record.hr_employee
            if employee.surname:
                full_name = employee.name + ' ' + employee.surname + ' /' + employee.pin + '/'
            else:
                full_name = employee.name + ' /' + employee.pin + '/'
            record.full_name = full_name

    @api.depends("start_work")
    def _compute_start_work_time(self):
        for record in self:
            if record.start_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(record.start_work).astimezone(local)
                hour = date_result.hour
                minute = date_result.minute
                record.start_work_time = hour + minute/60

    @api.depends("end_work")
    def _compute_end_work_time(self):
        for record in self:
            if record.end_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(record.end_work).astimezone(local)
                hour = date_result.hour
                minute = date_result.minute
                record.end_work_time = hour + minute/60

    @api.depends("check_in")
    def _compute_check_in_time(self):
        for record in self:
            if record.check_in:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(record.check_in).astimezone(local)
                record.check_in_time = "    " + datetime.strftime(date_result, "%H:%M")
            else:
                record.check_in_time = ''
    @api.depends("check_out")
    def _compute_check_out_time(self):
        for record in self:
            if record.check_out:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(record.check_out).astimezone(local)
                record.check_out_time = "    " + datetime.strftime(date_result, "%H:%M")
            else:
                record.check_out_time = ''

    @api.depends("paid_req_id")
    def _compute_paid_req_time(self):
        for record in self:
            if record.paid_req_id and (record.paid_req_id.state == 'validate' or record.paid_req_id.state == 'validate1'):
                check_out = record.check_out
                date_from = record.paid_req_id.date_from
                if not record.check_out or record.paid_req_id.date_to < record.check_out:
                    check_out = record.paid_req_id.date_to
                record.paid_req_time = self._diff_by_hours(date_from, check_out)

    @api.depends("unpaid_req_id")
    def _compute_unpaid_req_time(self):
        for record in self:
            if record.unpaid_req_id and (record.unpaid_req_id.state == 'validate' or record.unpaid_req_id.state == 'validate1'):
                check_out = record.check_out
                date_from = record.unpaid_req_id.date_from
                if not record.check_out or record.unpaid_req_id.date_to < record.check_out:
                    check_out = record.unpaid_req_id.date_to
                record.unpaid_req_time = self._diff_by_hours(date_from, check_out)

    @api.depends("vacation_req_id")
    def _compute_vacation_req_time(self):
        for record in self:
            if record.vacation_req_id and (record.vacation_req_id.state == 'validate' or record.vacation_req_id.state == 'validate1'):
                check_out = record.check_out
                date_from = record.vacation_req_id.date_from
                if not record.check_out or record.vacation_req_id.date_to < record.check_out:
                    check_out = record.vacation_req_id.date_to
                record.vacation_req_time = self._diff_by_hours(date_from, check_out)

    @api.depends("overtime_req_id")
    def _compute_overtime(self):
        for record in self:
            if record.overtime_req_id and (record.overtime_req_id.state == 'validate' or record.overtime_req_id.state == 'validate1'):
                check_out = record.check_out
                date_from = record.overtime_req_id.date_from
                date_to = record.overtime_req_id.date_to
                if record.check_out:
                    if date_to < record.check_out:
                        check_out = date_to
                    record.overtime = self._diff_by_hours(date_from, check_out)
                else:
                    record.overtime = self._diff_by_hours(date_from, date_to)

    @api.depends('overtime_req_id', 'check_out', "end_work", "attendance_req_id")
    def _compute_informal_overtime(self):
        for record in self:
            informal_overtime = 0.0
            if not record.check_out:
                informal_overtime = 0.0
            elif record.check_out < record.end_work:
                informal_overtime = 0.0
            else:
                delta = record.check_out - record.end_work
                informal_overtime = delta.total_seconds() / 3600.0

            if record.attendance_req_id and (record.attendance_req_id.state == 'validate' or record.attendance_req_id.state == 'validate1'):
                attendance_in_out = record.attendance_req_id.attendance_in_out
                print("attendance_in_out: ", record.attendance_req_id.attendance_in_out)
                if attendance_in_out == 'check_out':
                    date_to = record.attendance_req_id.date_to
                    print(date_to, record.end_work)
                    if date_to > record.end_work:
                        delta = date_to - record.end_work
                        informal_overtime = delta.total_seconds() / 3600.0
                        print("informal_overtime: ", informal_overtime)
                    else:
                        pass
                else:
                    pass

            if record.overtime_req_id and (record.overtime_req_id.state == 'validate' or record.overtime_req_id.state == 'validate1'):
                check_out = record.check_out
                date_from = record.overtime_req_id.date_from
                date_to = record.overtime_req_id.date_to
                if record.check_out:
                    if date_to < record.check_out:
                        check_out = date_to
                    informal_overtime += self._diff_by_hours(date_from, check_out)
                else:
                    informal_overtime += self._diff_by_hours(date_from, date_to)
            record.informal_overtime = informal_overtime

    @api.depends("attendance_req_id")
    def _compute_attendance_req(self):
        for record in self:
            if record.attendance_req_id and (record.attendance_req_id.state == 'validate' or record.attendance_req_id.state == 'validate1'):
                attendance_in_out = record.attendance_req_id.attendance_in_out
                if attendance_in_out == 'check_out':
                    check_in = record.check_in
                    date_to = record.attendance_req_id.date_to
                    record.attendance_req_time = self._diff_by_hours(check_in, date_to)
                elif attendance_in_out == 'check_in':
                    check_out = record.check_out
                    date_from = record.attendance_req_id.date_from
                    record.attendance_req_time = self._diff_by_hours(date_from, check_out)
                else:
                    pass

    @api.depends("outside_work_req_id")
    def _compute_outside_work(self):
        for record in self:
            if record.outside_work_req_id and (record.overtime_req_id.state == 'validate' or record.overtime_req_id.state == 'validate1'):
                check_out = record.check_out
                date_from = record.outside_work_req_id.date_from
                if not record.check_out or record.outside_work_req_id.date_to < record.check_out:
                    check_out = record.outside_work_req_id.date_to
                record.outside_work = self._diff_by_hours(date_from, check_out)

    @api.depends("check_in", "check_out")
    def _compute_take_off_day(self):
        for record in self:
            if not record.check_in and not record.check_out:
                record.take_off_day = 1
            else:
                record.take_off_day = 0

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

    # _compute_work_days

    @api.depends("start_work", "end_work")
    def _compute_work_days(self):
        for record in self:
            is_rest = True
            if record.shift_type == 'shift':
                is_rest = record.day_period.is_rest
            elif int(record.week_day) < 5:
                is_rest = False
            diff = record.lunch_time_to - record.lunch_time_from
            diff = diff.total_seconds() / 3600.0
            if is_rest:
                record.work_days = 0.0
            else:
                record.work_days = 1.0
                if record.work_hours < 0.0:
                    record.work_days = 0.0

    @api.depends("start_work", "end_work")
    def _compute_work_hours(self):
        for record in self:
            is_rest = True
            if record.shift_type == 'shift':
                is_rest = record.day_period.is_rest
            elif int(record.week_day) < 5:
                is_rest = False
            diff = record.lunch_time_to - record.lunch_time_from
            diff = diff.total_seconds() / 3600.0
            if is_rest:
                record.work_hours = 0.0
            else:
                record.work_hours = (record.end_work - record.start_work).total_seconds() / 3600 - diff
                if record.work_hours < 0.0:
                    record.work_hours = 0.0

    @api.depends('check_in', "start_work", 'check_out', "end_work", "day_period", "attendance_req_id")
    def _compute_worked_days(self):
        for record in self:
            is_rest = True
            is_rest = record.day_period.is_rest
            if record.shift_type == 'shift':
                is_rest = record.day_period.is_rest
            elif int(record.week_day) < 5:
                is_rest = False
            diff = record.lunch_time_to - record.lunch_time_from
            diff = diff.total_seconds() / 3600.0
            if is_rest:
                record.worked_days = 0.0
            else:
                if record.check_out and record.check_in:
                    record.worked_days = 1.0
                elif record.check_out:
                    record.worked_days = 1.0
                elif record.check_in:
                    record.worked_days = 1.0
                else:
                    if record.attendance_req_id and (record.attendance_req_id.state == 'validate' or record.attendance_req_id.state == 'validate1'):
                        record.worked_days = 1.0
                    else:
                        record.worked_days = 0.0

    @api.depends('check_in', "start_work", 'check_out', "end_work", "day_period", "attendance_req_id")
    def _compute_worked_hours(self):
        setting_obj = self.env['hr.attendance.settings'].search([], limit=1, order='id desc')
        for record in self:
            is_rest = True
            worked_hours = 0.0
            attendance_req_time = 0.0
            is_rest = record.day_period.is_rest
            if record.shift_type == 'shift':
                is_rest = record.day_period.is_rest
            elif int(record.week_day) < 5:
                is_rest = False
            diff = record.lunch_time_to - record.lunch_time_from
            diff = diff.total_seconds() / 3600.0
            if is_rest:
                worked_hours = 0.0
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
                    worked_hours = delta.total_seconds() / 3600.0 - diff
                elif record.check_out:
                    if record.check_out < record.end_work:
                        check_out = record.check_out
                    delta = check_out - check_in
                    worked_hours = delta.total_seconds() / 3600.0 - setting_obj.late_subtrack - diff
                elif record.check_in:
                    if record.start_work < record.check_in:
                        if (setting_obj.late_min * 3600) < (record.check_in - record.start_work).total_seconds():
                            check_in = record.check_in
                    delta = check_out - check_in
                    worked_hours = delta.total_seconds() / 3600.0 - setting_obj.late_subtrack - diff
                else:
                    worked_hours = 0.0
            if worked_hours < 0.0:
                worked_hours = 0.0

            record.worked_hours = worked_hours

            if record.attendance_req_id and (record.attendance_req_id.state == 'validate' or record.attendance_req_id.state == 'validate1'):
                attendance_in_out = record.attendance_req_id.attendance_in_out
                check_out = record.end_work
                if attendance_in_out == 'check_out':
                    check_in = record.check_in
                    date_to = record.attendance_req_id.date_to
                    if date_to < record.end_work:
                        check_out = date_to
                    attendance_req_time = self._diff_by_hours(check_in, check_out) - diff
                elif attendance_in_out == 'check_in':
                    if record.check_out < record.end_work:
                        check_out = record.check_out
                    date_from = record.attendance_req_id.date_from
                    attendance_req_time = self._diff_by_hours(date_from, check_out) - diff
                else:
                    pass
                record.worked_hours = attendance_req_time

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
        setting_obj = self.env['hr.attendance.settings'].search([], limit=1, order='id desc')
        employees = []
        if calculate_type == 'employee':
            for emp_id in employee_id:
                employees.append(emp_id.id)
        else:
            departments = self._get_departments(department_id, [])
            parents = department_id.ids[:]
            departments = departments + parents
            departments = list(dict.fromkeys(departments))

            if departments:
                for dep_id in departments:
                    self._cr.execute(
                        "SELECT DISTINCT employee_id AS hr_employee FROM hr_attendance WHERE department_id = "
                        +str(dep_id)+" AND check_in BETWEEN" '%s' " and " '%s',(start_date,end_date))
                    for t in self._cr.dictfetchall():
                        employees.append(t['hr_employee'])
            else:
                for dep_id in department_id:
                    self._cr.execute(
                        "SELECT DISTINCT employee_id AS hr_employee FROM hr_attendance WHERE department_id = "
                        +str(dep_id.id+" AND check_in BETWEEN" '%s' " and " '%s',(start_date,end_date)))
                    for t in self._cr.dictfetchall():
                        employees.append(t['hr_employee'])
        
        employees = list(dict.fromkeys(employees))
        
        data = []
        for employee_id in employees:
            dates_btwn = start_date

            all_schedules = self.env['hr.employee.schedule'].search([
            ('work_day', '>=', start_date),
            ('work_day', '<=', end_date),
            ('hr_employee', '=', employee_id),
            ])
            all_attendance_reqs = self.env['hr.leave'].search([
                ('date_from', '>=', start_date),
                ('date_from', '<=', end_date),
                ('employee_id', '=', employee_id),
            ])

            self.env['hr.attendance.report'].search([('work_day', '>=', start_date), ('work_day', '<=', end_date), ('hr_employee', '=', employee_id)]).unlink()
            while dates_btwn <= end_date:
                schedules = all_schedules.search([
                    ('work_day', '=', dates_btwn),
                    ('hr_employee', '=', employee_id),
                ])
                for schedule in schedules:
                    values = {}
                    if schedule:
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

                    if values['shift_type'] == 'shift':
                        date_from = datetime.combine(dates_btwn, time())
                        date_to = datetime.combine(dates_btwn, time())
                        date_to = date_to + timedelta(hours=23, minutes=59, seconds=59)
                        
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
                    if not attendances and values['shift_type'] == 'days':
                        date_from = datetime.combine(dates_btwn, time())
                        date_from = date_from + timedelta(seconds=setting_obj.end_work_date_from * 3600)
                        date_to = datetime.combine(dates_btwn, time())
                        date_to = date_to + timedelta(days=1) + timedelta(seconds=setting_obj.end_work_date_to * 3600 + 59)

                        attendances = self.env['hr.attendance'].search([
                            ('check_in', '>=', self._convert_datetime_field(date_from)),
                            ('check_in', '<=', self._convert_datetime_field(date_to)),
                            ('employee_id', '=', employee_id),
                        ])

                    for attendance in attendances:
                        if attendance:
                            values['hr_attendance'] = attendance.id
                            values['check_in'] = attendance.check_in
                            values['check_out'] = attendance.check_out
                            values['worked_hours'] = attendance.worked_hours

                    date_from = datetime.combine(dates_btwn, time())
                    date_to = datetime.combine(dates_btwn, time())
                    date_to = date_to + timedelta(hours=23, minutes=59, seconds=59)

                    attendance_reqs = all_attendance_reqs.search([
                        ('date_from', '>=', self._convert_datetime_field(date_from)),
                        ('date_from', '<=', self._convert_datetime_field(date_to)),
                        ('employee_id', '=', employee_id),
                        # ('holiday_type', '=', 'employee'),
                    ])

                    for attendance_req in attendance_reqs:
                        req_type = attendance_req.holiday_status_id.request_status_type
                        if req_type == 'overtime':
                            values['overtime_req_id'] = attendance_req.id
                        elif req_type == 'outside_work':
                            values['outside_work_req_id'] = attendance_req.id
                        elif req_type == 'paid':
                            values['paid_req_id'] = attendance_req.id
                        elif req_type == 'unpaid':
                            values['unpaid_req_id'] = attendance_req.id
                        elif req_type == 'vacation':
                            values['vacation_req_id'] = attendance_req.id
                        elif req_type == 'attendance':
                            values['attendance_req_id'] = attendance_req.id

                    data.append(values)
                    super(HrAttendanceReport, self).create(values)
                dates_btwn = dates_btwn + relativedelta(days=1)
        header = [
            'hr_department', 
            'hr_employee', 
            'hr_employee_shift', 
            'hr_employee_schedule', 
            'hr_employee_shift_template', 
            'hr_employee_shift_dayplan', 
            'date_from', 
            'date_to', 
            'work_day', 
            'shift_type', 
            'week_day', 
            'day_period', 
            'day_period_int', 
            'lunch_time_from', 
            'lunch_time_to', 
            'start_work', 
            'end_work', 
            'hr_attendance',
            'check_in',
            'check_out',
            'worked_hours',
            'overtime_req_id',
            'outside_work_req_id',
            'leave_id'
        ]
        return [header, data]


    @api.model
    def get_attendances_report(self, filters):
        start_date = filters['start_date']
        end_date = filters['end_date']
        
        if filters['calculate_type']:
            if filters['calculate_type'] == 'employee':
                employee_id = filters['employee_id']
                domain = [('hr_employee', '=', employee_id), ('work_day', '>=', start_date), ('work_day', '<=', end_date)]
            else:
                department_id = filters['department_id']
                dep = self.env['hr.department'].browse(department_id)
                departments = self._get_departments(dep, [])
                parents = dep.ids[:]
                departments = departments + parents
                departments = list(dict.fromkeys(departments))
                domain = [('hr_department', '=', departments), ('work_day', '>=', start_date), ('work_day', '<=', end_date)]
        else:
            domain = [('work_day', '>=', start_date), ('work_day', '<=', end_date)]

        att_report_onj = self.env['hr.attendance.report']
        raw_data = att_report_onj.read_group(
            domain=domain,
            fields=[
                'hr_employee_shift',
                'work_days', 
                'work_hours', 
                'worked_days', 
                'worked_hours', 
                'overtime', 
                'informal_overtime', 
                'paid_req_time', 
                'unpaid_req_time', 
                'take_off_day', 
                'difference_check_out', 
                'difference_check_in'
            ],
            groupby=['full_name', 'hr_department', 'hr_employee', 'hr_employee_shift'], 
            lazy=False
        )

        header = [
            ['full_name', 'Нэр овог'], 
            ['hr_employee_shift', 'Ажиллах хуваарь'], 
            ['work_days', 'Ажиллавал зохих өдөр'], 
            ['work_hours', 'Ажиллавал зохих цаг'], 
            ['worked_days', 'Ажилласан өдөр'], 
            ['worked_hours', 'Ажилласан цаг'], 
            ['overtime', 'Баталсан илүү цаг'], 
            ['informal_overtime', 'Нийт илүү цаг'], 
            ['paid_req_time', 'Цалинтай чөлөө'], 
            ['unpaid_req_time', 'Цалингүй чөлөө'], 
            ['take_off_day', 'Тасалсан өдөр'],
            ['difference_check_out', 'Таслалт'], 
            ['difference_check_in', 'Хоцролт']
        ]

        data = {
            'data': raw_data,
            'header': header
        }
        return data

    @api.model
    def get_attendances_report_total(self, filters):
        start_date = filters['start_date']
        end_date = filters['end_date']
        
        if filters['calculate_type']:
            if filters['calculate_type'] == 'employee':
                employee_id = filters['employee_id']
                domain = [('hr_employee', '=', employee_id.id), ('work_day', '>=', start_date), ('work_day', '<=', end_date)]
            else:
                department_id = filters['department_id']
                dep = self.env['hr.department'].browse(department_id)
                departments = self._get_departments(dep, [])
                parents = dep.ids[:]
                departments = departments + parents
                departments = list(dict.fromkeys(departments))
                domain = [('hr_department', '=', departments), ('work_day', '>=', start_date), ('work_day', '<=', end_date)]
        else:
            domain = [('work_day', '>=', start_date), ('work_day', '<=', end_date)]

        att_report_onj = self.env['hr.attendance.report']
        raw_data = att_report_onj.read_group(
            domain=domain,
            fields=[
                'hr_employee_shift',
                'work_days', 
                'work_hours', 
                'worked_days', 
                'worked_hours', 
                'overtime', 
                'informal_overtime', 
                'paid_req_time', 
                'unpaid_req_time', 
                'take_off_day', 
                'difference_check_out', 
                'difference_check_in'
            ],
            groupby=['full_name', 'hr_department', 'hr_employee', 'hr_employee_shift'], 
            lazy=False
        )

        header = [
            ['full_name', 'Нэр овог'], 
            ['hr_employee_shift', 'Ажиллах хуваарь'], 
            ['work_days', 'Ажиллавал зохих өдөр'], 
            ['work_hours', 'Ажиллавал зохих цаг'], 
            ['worked_days', 'Ажилласан өдөр'], 
            ['worked_hours', 'Ажилласан цаг'], 
            ['overtime', 'Баталсан илүү цаг'], 
            ['informal_overtime', 'Нийт илүү цаг'], 
            ['paid_req_time', 'Цалинтай чөлөө'], 
            ['unpaid_req_time', 'Цалингүй чөлөө'], 
            ['take_off_day', 'Тасалсан өдөр'],
            ['difference_check_out', 'Таслалт'], 
            ['difference_check_in', 'Хоцролт']
        ]

        data = {
            'data': raw_data,
            'header': header,
            'filters': filters,
            'type': 0
        }
        return data

    @api.model
    def get_attendances_report_detail(self, filters):
        start_date = filters['start_date']
        end_date = filters['end_date']
        
        if filters['calculate_type']:
            if filters['calculate_type'] == 'employee':
                employee_id = filters['employee_id']
                domain = [('hr_employee', '=', employee_id.id), ('work_day', '>=', start_date), ('work_day', '<=', end_date)]
            else:
                department_id = filters['department_id']
                dep = self.env['hr.department'].browse(department_id)
                departments = self._get_departments(dep, [])
                parents = dep.ids[:]
                departments = departments + parents
                departments = list(dict.fromkeys(departments))
                domain = [('hr_department', '=', departments), ('work_day', '>=', start_date), ('work_day', '<=', end_date)]
        else:
            domain = [('work_day', '>=', start_date), ('work_day', '<=', end_date)]

        att_report_obj = self.env['hr.attendance.report'].search(domain)
        raw_data = att_report_obj.read([
            'full_name',
            'work_day',
            'hr_employee',
            'hr_department',
            # 'hr_employee_shift',
            'work_days', 
            'work_hours', 
            'worked_days', 
            'worked_hours', 
            'overtime', 
            'informal_overtime',
            'paid_req_time', 
            'unpaid_req_time', 
            'take_off_day', 
            'difference_check_out', 
            'difference_check_in',
            'check_in',
            'check_out'
        ])

        header = [
            ['full_name', 'Нэр овог'], 
            ['work_day', 'Огноо'], 
            # ['hr_employee_shift', 'Ажиллах хуваарь'], 
            ['work_days', 'Ажиллавал зохих өдөр'], 
            ['work_hours', 'Ажиллавал зохих цаг'], 
            ['check_in', 'Орсон'], 
            ['check_out', 'Гарсан'], 
            ['worked_days', 'Ажилласан өдөр'], 
            ['worked_hours', 'Ажилласан цаг'], 
            ['overtime', 'Баталсан илүү цаг'], 
            ['informal_overtime', 'Нийт илүү цаг'],
            ['paid_req_time', 'Цалинтай чөлөө'], 
            ['unpaid_req_time', 'Цалингүй чөлөө'], 
            ['take_off_day', 'Тасалсан өдөр'],
            ['difference_check_out', 'Таслалт'], 
            ['difference_check_in', 'Хоцролт']
        ]

        data = {
            'data': raw_data,
            'header': header,
            'filters': filters,
            'type': 1
        }
        return data

    @api.model
    def get_my_attendances_report(self, filters):
        att_report_obj = self.env['hr.attendance.report']
        row = []
        header = [['field_name', 0]]
        employee_id = filters['employee_id']
        
        DATE_FORMAT = '%Y-%m-%d'
        start_date = datetime.strptime(filters['start_date'], DATE_FORMAT).date()
        end_date = datetime.strptime(filters['end_date'], DATE_FORMAT).date()
        dates_btwn = start_date
        while dates_btwn <= end_date:
            if dates_btwn.weekday() < 5:
                header.append([dates_btwn, 0])
            else:
                header.append([dates_btwn, 1])
            dates_btwn = dates_btwn + relativedelta(days=1)

        fields = [
            ['work_hours', 'Ажиллавал зохих цаг'], 
            ['worked_hours', 'Ажилласан цаг'], 
            ['overtime', 'Баталсан илүү цаг'], 
            ['informal_overtime', 'Нийт илүү цаг'],
            ['paid_req_time', 'Цалинтай чөлөө'], 
            ['unpaid_req_time', 'Цалингүй чөлөө'], 
            ['difference_check_out', 'Таслалт'], 
            ['difference_check_in', 'Хоцролт']
        ]

        for f in fields:
            arr = {}
            arr['field_name'] = f[1]
            dates_btwn = start_date
            while dates_btwn <= end_date:
                raw_data = att_report_obj.read_group(
                    domain=[('hr_employee', '=', employee_id), ('work_day', '=', dates_btwn)],
                    fields=[f[0]],
                    groupby=[], 
                    lazy=False
                )
                arr[str(dates_btwn)] = raw_data
                dates_btwn = dates_btwn + relativedelta(days=1)
            row.append(arr)

        data = {
            'data': row,
            'header': header,
            'fields': fields
        }
        return data