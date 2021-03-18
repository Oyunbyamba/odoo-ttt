# -*- coding: utf-8 -*-

import pytz
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, time
import xlsxwriter
import io
import xlwt
import base64
import logging
import pandas as pd

_logger = logging.getLogger(__name__)


class HrAttendanceReport(models.Model):
    """Ирцийн тайлан гаргахад шаардлагатай өгөгдөл хадгалах хүснэгт"""
    _name = 'hr.attendance.report'
    _description = 'Hr Attendance Report'

    hr_department = fields.Many2one(
        'hr.department', string="Department", help="Department")
    hr_employee = fields.Many2one(
        'hr.employee', string="Employee", help="Employee")
    hr_employee_shift = fields.Many2one(
        'hr.employee.shift', string="Employee Shift", help="Employee Shift")
    hr_employee_schedule = fields.Many2one(
        'hr.employee.schedule', string="Employee Schedule", help="Employee Schedule")
    hr_attendance = fields.Many2one(
        'hr.attendance', string="Employee Attendance", help="Employee Attendance")
    hr_employee_shift_template = fields.Many2one(
        'resource.calendar', 'Employee Shift Template')
    hr_employee_shift_dayplan = fields.Many2one(
        'resource.calendar.shift', 'Employee Shift Plan of Day')
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
    day_period = fields.Many2one(
        'resource.calendar.dayperiod', string="Day Period", help="Day Period of Work")
    day_period_int = fields.Integer(
        string='Day Period Integer', help='Day Period of Work')
    lunch_time_from = fields.Datetime(string='Lunch time from')
    lunch_time_to = fields.Datetime(string='Lunch time to')
    start_work = fields.Datetime(string="Start Work")
    end_work = fields.Datetime(string="End Work")

    check_in = fields.Datetime(string="Check In")
    check_out = fields.Datetime(string="Check Out")
    work_days = fields.Float(string='Must Worked Days',
                             compute="_compute_work_days", store=True, compute_sudo=True)
    work_hours = fields.Float(string='Must Worked Hours',
                              compute="_compute_work_hours", store=True, compute_sudo=True)
    worked_days = fields.Float(
        string='Worked Days', compute="_compute_worked_days", store=True, compute_sudo=True)
    worked_hours = fields.Float(
        string='Worked Hours', compute="_compute_worked_hours", store=True, compute_sudo=True)

    overtime_holiday = fields.Float(
        string='Holyday Overtime Hours', compute="_compute_overtime_holiday", store=True, compute_sudo=True)

    formal_worked_hours = fields.Float(
        string='Formal Worked Hours', compute="_compute_formal_worked_hours", store=True, compute_sudo=True)

    difference_check_in = fields.Float(
        compute="_compute_difference_check_in", store=True, compute_sudo=True)
    difference_check_out = fields.Float(
        compute="_compute_difference_check_out", store=True, compute_sudo=True)
    take_off_day = fields.Integer(
        compute="_compute_take_off_day", store=True, compute_sudo=True)

    paid_req_id = fields.Many2one('hr.leave')
    unpaid_req_id = fields.Many2one('hr.leave')
    vacation_req_id = fields.Many2one('hr.leave')
    overtime_req_id = fields.Many2one('hr.leave')
    outside_work_req_id = fields.Many2one('hr.leave')
    attendance_req_id = fields.Many2many('hr.leave')

    paid_req_time = fields.Float(
        compute="_compute_paid_req_time", store=True, compute_sudo=True)
    unpaid_req_time = fields.Float(
        compute="_compute_unpaid_req_time", store=True, compute_sudo=True)
    vacation_req_time = fields.Float(
        compute="_compute_vacation_req_time", store=True, compute_sudo=True)
    overtime = fields.Float(compute="_compute_overtime",
                            store=True, compute_sudo=True)
    informal_overtime = fields.Float(
        compute="_compute_informal_overtime", store=True, compute_sudo=True)
    outside_work = fields.Float(
        compute="_compute_outside_work", store=True, compute_sudo=True)
    attendance_req_time = fields.Float(
        compute="_compute_attendance_req", store=True, compute_sudo=True)

    check_in_time = fields.Char(
        compute="_compute_check_in_time", compute_sudo=True)
    check_out_time = fields.Char(
        compute="_compute_check_out_time", compute_sudo=True)
    start_work_time = fields.Float(
        compute="_compute_start_work_time", compute_sudo=True)
    end_work_time = fields.Float(
        compute="_compute_end_work_time", compute_sudo=True)

    full_name = fields.Char(compute="_compute_full_name",
                            store=True, compute_sudo=True)
    ceo_approved_overtime = fields.Float(
        compute="_compute_ceo_approved_overtime", store=True, compute_sudo=True)

    global_leaves = fields.One2many(
        related='hr_employee.resource_calendar_id.global_leave_ids')
    register_id = fields.Char(
        related='hr_employee.identification_id', store=True,)

    @api.depends("hr_employee")
    def _compute_full_name(self):
        for record in self:
            if record.hr_employee:
                employee = record.hr_employee
                if not employee.pin:
                    pin = ''
                else:
                    pin = ' /' + employee.pin + '/'
                if employee.surname:
                    full_name = employee.name + ' ' + employee.surname + pin
                else:
                    full_name = employee.name + pin

                record.full_name = full_name

    @api.depends("start_work")
    def _compute_start_work_time(self):
        for record in self:
            if record.start_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(
                    record.start_work).astimezone(local)
                hour = date_result.hour
                minute = date_result.minute
                record.start_work_time = hour + minute/60

    @api.depends("end_work")
    def _compute_end_work_time(self):
        for record in self:
            if record.end_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(
                    record.end_work).astimezone(local)
                hour = date_result.hour
                minute = date_result.minute
                record.end_work_time = hour + minute/60

    @api.depends("check_in")
    def _compute_check_in_time(self):
        for record in self:
            if record.check_in:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(
                    record.check_in).astimezone(local)
                record.check_in_time = "    " + \
                    datetime.strftime(date_result, "%H:%M")
            else:
                record.check_in_time = ''

    @api.depends("check_out")
    def _compute_check_out_time(self):
        for record in self:
            if record.check_out:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(
                    record.check_out).astimezone(local)
                record.check_out_time = "    " + \
                    datetime.strftime(date_result, "%H:%M")
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
                record.paid_req_time = self._diff_by_hours(
                    date_from, check_out)

    @api.depends("unpaid_req_id")
    def _compute_unpaid_req_time(self):
        for record in self:
            if record.unpaid_req_id and (record.unpaid_req_id.state == 'validate' or record.unpaid_req_id.state == 'validate1'):
                check_out = record.check_out
                date_from = record.unpaid_req_id.date_from
                if not record.check_out or record.unpaid_req_id.date_to < record.check_out:
                    check_out = record.unpaid_req_id.date_to
                record.unpaid_req_time = self._diff_by_hours(
                    date_from, check_out)

    @api.depends("vacation_req_id")
    def _compute_vacation_req_time(self):
        for record in self:
            if record.vacation_req_id and (record.vacation_req_id.state == 'validate' or record.vacation_req_id.state == 'validate1'):
                check_out = record.check_out
                date_from = record.vacation_req_id.date_from
                if not record.check_out or record.vacation_req_id.date_to < record.check_out:
                    check_out = record.vacation_req_id.date_to
                record.vacation_req_time = self._diff_by_hours(
                    date_from, check_out)

    @api.depends("check_in", "check_out", "hr_employee")
    def _compute_ceo_approved_overtime(self):
        for record in self:
            ceo_approved_overtime = 0.0
            approved_overtimes = self.env['hr.leave'].sudo().search([
                ('date_from', '<=', record.check_in),
                ('date_to', '>=', record.check_out),
                ('employee_id', '=', False)
            ])
            for app in approved_overtimes:
                if record.hr_employee.department_id == app.department_id and app.holiday_status_id.request_status_type == 'overtime' and app.holiday_status_id.overtime_type == 'total_allowed_overtime':
                    record.ceo_approved_overtime = app.allowed_overtime_time

    @api.depends("overtime_req_id")
    def _compute_overtime(self):
        for record in self:
            if record.overtime_req_id.holiday_status_id.request_status_type == 'overtime' and record.overtime_req_id.holiday_status_id.overtime_type != 'manager_proved_overtime' and (record.overtime_req_id.state == 'validate' or record.overtime_req_id.state == 'validate1'):
                check_out = record.check_out
                date_from = record.overtime_req_id.date_from
                date_to = record.overtime_req_id.date_to
                if record.check_out:
                    if date_to < record.check_out:
                        check_out = date_to
                    record.overtime = self._diff_by_hours(date_from, check_out)
                else:
                    record.overtime = self._diff_by_hours(date_from, date_to)

            if record.overtime_req_id.holiday_status_id.request_status_type == 'overtime' and record.overtime_req_id.holiday_status_id.overtime_type == 'manager_proved_overtime' and (record.overtime_req_id.state == 'validate' or record.overtime_req_id.state == 'validate1'):
                record.overtime = record.overtime_req_id.allowed_overtime_time

    @ api.depends("worked_hours", "shift_type", "check_in", "check_out")
    def _compute_overtime_holiday(self):
        for record in self:
            overtime_holiday = 0.0
            holiday = False
            if record.worked_hours and record.shift_type == 'days':
                for leaves in record.global_leaves:
                    leave_dates = pd.date_range(
                        leaves.date_from+relativedelta(hours=8), leaves.date_to + relativedelta(hours=8),).date
                    if record.check_in and record.check_out:
                        holiday_dates = pd.date_range(
                            record.check_in + relativedelta(hours=8), record.check_out + relativedelta(hours=8)).date
                    elif record.check_in:
                        holiday_dates = pd.date_range(
                            record.check_in + relativedelta(hours=8), record.check_in + relativedelta(hours=8)).date
                    elif record.check_out:
                        holiday_dates = pd.date_range(
                            record.check_out + relativedelta(hours=8), record.check_out + relativedelta(hours=8)).date
                    for hd in holiday_dates:

                        for leave_date in leave_dates:
                            if leave_date == hd:
                                holiday = True
            if holiday:
                overtime_holiday = record.worked_hours
                record.overtime_holiday = overtime_holiday

    @ api.depends('overtime_req_id', 'check_in', 'check_out', 'start_work', "end_work", "attendance_req_id", "overtime", "overtime_holiday")
    def _compute_informal_overtime(self):
        for record in self:
            informal_overtime = 0.0

            if record.overtime_holiday > 0 and record.shift_type == 'days':
                record.informal_overtime = record.overtime_holiday
                return

            if record.take_off_day == 1:
                record.informal_overtime = 0.0
                return

            is_rest = True
            if record.shift_type == 'shift':
                is_rest = record.day_period.is_rest
            elif int(record.week_day) < 5:
                is_rest = False

            if not record.start_work or not record.end_work:
                is_rest = True

            if is_rest:
                informal_overtime = 0.0
                if record.hr_employee_schedule.id == 0:
                    if record.check_out and record.check_in:
                        delta = record.check_out - record.check_in
                        informal_overtime = delta.total_seconds() / 3600.0
            else:
                if not record.check_out:
                    informal_overtime = 0.0
                # ali 1 taldaa huruu daraagui bol iluu tsag bodohgui
                elif not record.check_in:
                    informal_overtime += 0.0
                elif record.check_in and record.check_out < record.end_work:
                    informal_overtime = 0.0
                else:
                    delta = record.check_out - record.end_work
                    informal_overtime += delta.total_seconds() / 3600.0

                # by Sainaa ugluu ert irseng tootsohgui

                if record.attendance_req_id and (record.overtime > 0 or record.overtime_holiday > 0):
                    record.informal_overtime = 0.0
                    # by Sainaa iluu tsagiig davharduulahguin tuld batlagdsan bolon bayar yosloliin udriig hasna
                    # for req_id in record.attendance_req_id:
                    #     attendance_in_out = req_id.attendance_in_out
                    #     if attendance_in_out == 'check_out':
                    #         date_to = req_id.date_to
                    #         if record.hr_employee_schedule.id != 0:
                    #             if date_to > record.end_work:
                    #                 delta = date_to - record.end_work
                    #                 informal_overtime = delta.total_seconds() / 3600.0
                    #         elif record.check_in:
                    #             delta = date_to - record.check_in
                    #             informal_overtime = delta.total_seconds() / 3600.0
                    #     if attendance_in_out == 'check_in':
                    #         date_from = req_id.date_from
                    #         if record.hr_employee_schedule.id != 0:
                    #             if date_from < record.start_work:
                    #                 delta = record.start_work - date_from
                    #                 informal_overtime = delta.total_seconds() / 3600.0
                    #         elif record.check_out:
                    #             delta = record.check_out - date_from
                    #             informal_overtime = delta.total_seconds() / 3600.0

                # if record.overtime_req_id and (record.overtime_req_id.state == 'validate' or record.overtime_req_id.state == 'validate1'):
                #     check_out = record.check_out
                #     date_from = record.overtime_req_id.date_from
                #     date_to = record.overtime_req_id.date_to
                #     if record.check_out:
                #         if date_to < record.check_out:
                #             check_out = date_to
                #         informal_overtime += self._diff_by_hours(date_from, check_out)
                #     else:
                #         informal_overtime += self._diff_by_hours(date_from, date_to)

            record.informal_overtime = informal_overtime

    @ api.depends("attendance_req_id")
    def _compute_attendance_req(self):
        for record in self:
            if record.attendance_req_id:
                check_in = record.check_in
                check_out = record.check_out
                for req_id in record.attendance_req_id:
                    attendance_in_out = req_id.attendance_in_out
                    if attendance_in_out == 'check_out':
                        check_out = req_id.date_to
                    elif attendance_in_out == 'check_in':
                        check_in = req_id.date_from
                if check_out and check_in:
                    record.attendance_req_time = self._diff_by_hours(
                        check_in, check_out)

    @ api.depends("outside_work_req_id")
    def _compute_outside_work(self):
        for record in self:
            if record.outside_work_req_id and (record.overtime_req_id.state == 'validate' or record.overtime_req_id.state == 'validate1'):
                check_out = record.check_out
                date_from = record.outside_work_req_id.date_from
                if not record.check_out or record.outside_work_req_id.date_to < record.check_out:
                    check_out = record.outside_work_req_id.date_to
                record.outside_work = self._diff_by_hours(date_from, check_out)

    @ api.depends("check_in", "check_out", "difference_check_in", "work_days")
    def _compute_take_off_day(self):
        for record in self:

            if record.hr_employee_schedule.id == 0:
                record.take_off_day = 0
            else:
                if record.work_days == 0.0:
                    record.take_off_day = 0
                    return
                if (record.difference_check_in * 3600) > 120:
                    record.take_off_day = 1
                if not record.check_in and not record.check_out:
                    record.take_off_day = 1
                else:
                    record.take_off_day = 0

    @ api.depends("check_in", "start_work", "difference_check_out", "overtime_holiday")
    def _compute_difference_check_in(self):
        setting_obj = self.env['hr.attendance.settings'].search(
            [], limit=1, order='id desc')
        for record in self:
            if record.overtime_holiday > 0 and record.shift_type == 'days':
                record.difference_check_in = 0
                return

            if record.hr_employee_schedule.id == 0:
                record.difference_check_in = 0
            else:
                if record.check_in:
                    if record.start_work >= record.check_in:
                        record.difference_check_in = 0
                    elif (setting_obj.late_min * 3600) >= (record.check_in - record.start_work).total_seconds():
                        record.difference_check_in = 0
                    else:
                        record.difference_check_in = self._diff_by_hours(
                            record.start_work, record.check_in)
                else:
                    record.difference_check_in = 0
            # ert garch yavsang hotsorson tsagt oruulna
            if record.difference_check_out > 0:
                record.difference_check_in += record.difference_check_out

    @ api.depends("check_out", "end_work", "overtime_holiday")
    def _compute_difference_check_out(self):
        for record in self:

            if record.overtime_holiday > 0 and record.shift_type == 'days':
                record.difference_check_in = 0
                return

            if record.hr_employee_schedule.id == 0:
                record.difference_check_out = 0
            else:
                if record.check_out:
                    if record.check_out >= record.end_work:
                        record.difference_check_out = 0
                    else:
                        record.difference_check_out = self._diff_by_hours(
                            record.check_out, record.end_work)
                else:
                    record.difference_check_out = 0

    @ api.depends("start_work", "end_work")
    def _compute_work_days(self):
        for record in self:
            is_rest = True
            if record.shift_type == 'shift':
                is_rest = record.day_period.is_rest
            elif int(record.week_day) < 5:
                holiday = False
                if record.start_work:
                    for leaves in record.global_leaves:
                        leave_dates = pd.date_range(
                            leaves.date_from+relativedelta(hours=8), leaves.date_to + relativedelta(hours=8),).date

                        holiday_dates = pd.date_range(
                            record.start_work + relativedelta(hours=8), record.start_work + relativedelta(hours=8)).date
                        for hd in holiday_dates:
                            for leave_date in leave_dates:
                                if leave_date == hd:
                                    holiday = True
                if holiday:
                    is_rest = True
                else:
                    is_rest = False
            if is_rest:
                record.work_days = 0.0
            else:
                record.work_days = 1.0
                if record.work_hours < 0.0:
                    record.work_days = 0.0

    @ api.depends("start_work", "end_work", "work_days")
    def _compute_work_hours(self):
        for record in self:
            is_rest = True
            if record.shift_type == 'shift':
                is_rest = record.day_period.is_rest
            elif int(record.week_day) < 5:
                if record.work_days == 0.0:
                    record.work_hours = 0.0
                    return

                is_rest = False
            if not record.lunch_time_to or not record.lunch_time_from:
                diff = 0.0
            else:
                diff = record.lunch_time_to - record.lunch_time_from
                diff = diff.total_seconds() / 3600.0
            if is_rest:
                record.work_hours = 0.0
            else:
                if record.end_work and record.start_work:
                    record.work_hours = (
                        record.end_work - record.start_work).total_seconds() / 3600 - diff
                    if record.work_hours < 0.0:
                        record.work_hours = 0.0
                else:
                    record.work_hours = 0.0

    @ api.depends('check_in', "start_work", 'check_out', "end_work", "day_period", "attendance_req_id")
    def _compute_worked_days(self):
        for record in self:
            is_rest = True
            if record.shift_type == 'shift':
                is_rest = record.day_period.is_rest
            elif int(record.week_day) < 5:
                is_rest = False
            if is_rest:
                # record.worked_days = 0.0
                # if record.hr_employee_schedule.id == 0 and (record.check_out or record.check_in):
                #     record.worked_days = 1.0
                pass
            else:
                if record.check_out and record.check_in:
                    record.worked_days = 1.0
                elif record.check_out:
                    record.worked_days = 1.0
                elif record.check_in:
                    record.worked_days = 1.0
                else:
                    if record.attendance_req_id:
                        record.worked_days = 1.0
                    else:
                        record.worked_days = 0.0

    @ api.depends('check_in', "start_work", 'check_out', "end_work", "day_period", "attendance_req_id", "take_off_day")
    def _compute_formal_worked_hours(self):
        setting_obj = self.env['hr.attendance.settings'].search(
            [], limit=1, order='id desc')
        for record in self:
            is_rest = True
            worked_hours = 0.0
            attendance_req_time = 0.0
            if record.take_off_day == 1:
                formal_worked_hours = 0.0
                return
            if record.shift_type == 'shift':
                is_rest = record.day_period.is_rest
            elif int(record.week_day) < 5:
                is_rest = False

            if not record.start_work or not record.end_work:
                is_rest = True

            if not record.lunch_time_to or not record.lunch_time_from:
                diff = 0.0
            else:
                diff = record.lunch_time_to - record.lunch_time_from
                diff = diff.total_seconds() / 3600.0

            if not is_rest:
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
            if worked_hours < 0.0:
                worked_hours = 0.0

            record.formal_worked_hours = worked_hours

            if not is_rest and record.attendance_req_id:
                check_in = record.check_in
                check_out = record.check_out
                subtract = 0.0
                for req_id in record.attendance_req_id:
                    attendance_in_out = req_id.attendance_in_out
                    if attendance_in_out == 'check_out':
                        check_out = req_id.date_to
                    elif attendance_in_out == 'check_in':
                        check_in = req_id.date_from
                if not check_in and record.hr_employee_schedule.id != 0:
                    check_in = record.start_work
                    subtract = setting_obj.late_subtrack
                if not check_out and record.hr_employee_schedule.id != 0:
                    check_out = record.end_work
                    subtract = setting_obj.late_subtrack
                attendance_req_time = self._diff_by_hours(
                    check_in, check_out) - diff - subtract
                if attendance_req_time < 0.0:
                    attendance_req_time = 0.0
                record.formal_worked_hours = attendance_req_time

    @api.depends('check_in', "start_work", 'check_out', "end_work", "day_period", "attendance_req_id")
    def _compute_worked_hours(self):
        setting_obj = self.env['hr.attendance.settings'].search(
            [], limit=1, order='id desc')
        for record in self:
            is_rest = True
            worked_hours = 0.0
            attendance_req_time = 0.0
            if record.shift_type == 'shift':
                is_rest = record.day_period.is_rest
            elif int(record.week_day) < 5:
                is_rest = False

            if not record.start_work or not record.end_work:
                is_rest = True

            if not record.lunch_time_to or not record.lunch_time_from:
                diff = 0.0
            else:
                diff = record.lunch_time_to - record.lunch_time_from
                diff = diff.total_seconds() / 3600.0

            if is_rest:
                worked_hours = 0.0
                if record.hr_employee_schedule.id == 0:
                    if record.check_out and record.check_in:
                        delta = record.check_out - record.check_in
                        worked_hours = delta.total_seconds() / 3600.0 - diff
            else:
                check_in = record.start_work
                check_out = record.end_work
                if record.check_out and record.check_in:
                    # ajildaa ert irsen eseh
                    if record.check_in > record.start_work:
                        check_in = record.check_in
                    else:
                        check_in = record.start_work
                    check_out = record.check_out
                    delta = check_out - check_in
                    worked_hours = delta.total_seconds() / 3600.0 - diff

                elif record.check_out:
                    record.check_out
                    delta = check_out - check_in
                    worked_hours = delta.total_seconds() / 3600.0 - setting_obj.late_subtrack - diff
                elif record.check_in:
                    if record.check_in > record.start_work:
                        check_in = record.check_in
                    else:
                        check_in = record.start_work
                    delta = check_out - check_in
                    worked_hours = delta.total_seconds() / 3600.0 - setting_obj.late_subtrack - diff
                else:
                    worked_hours = 0.0
            if worked_hours < 0.0:
                worked_hours = 0.0

            record.worked_hours = worked_hours

            if record.attendance_req_id:
                check_in = record.check_in
                check_out = record.check_out
                subtract = 0.0
                for req_id in record.attendance_req_id:
                    attendance_in_out = req_id.attendance_in_out
                    if attendance_in_out == 'check_out':
                        check_out = req_id.date_to
                    elif attendance_in_out == 'check_in':
                        check_in = req_id.date_from
                if not check_in and record.hr_employee_schedule.id != 0:
                    check_in = record.start_work
                    subtract = setting_obj.late_subtrack
                if not check_out and record.hr_employee_schedule.id != 0:
                    check_out = record.end_work
                    subtract = setting_obj.late_subtrack
                attendance_req_time = self._diff_by_hours(
                    check_in, check_out) - diff - subtract
                if attendance_req_time < 0.0:
                    attendance_req_time = 0.0
                record.worked_hours = attendance_req_time

    def _diff_by_hours(self, date1, date2):
        date = (date2 - date1).total_seconds()
        return date / 3600

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

    def _find_week_day_index(self, week_day):
        week = {
            'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6
        }
        return week.get(week_day, -1)

    def calculate_report(self, start_date, end_date, calculate_type, department_id, employee_id):
        setting_obj = self.env['hr.attendance.settings'].search(
            [], limit=1, order='id desc')
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
                        + str(dep_id)+" AND check_in BETWEEN" '%s' " and " '%s', (start_date, end_date))
                    for t in self._cr.dictfetchall():
                        employees.append(t['hr_employee'])
            else:
                for dep_id in department_id:
                    self._cr.execute(
                        "SELECT DISTINCT employee_id AS hr_employee FROM hr_attendance WHERE department_id = "
                        + str(dep_id.id+" AND check_in BETWEEN" '%s' " and " '%s', (start_date, end_date)))
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

            self.env['hr.attendance.report'].search([('work_day', '>=', start_date), (
                'work_day', '<=', end_date), ('hr_employee', '=', employee_id)]).unlink()

            while dates_btwn <= end_date:
                schedules = all_schedules.search([
                    ('work_day', '=', dates_btwn),
                    ('hr_employee', '=', employee_id),
                ])
                emp = self.env["hr.employee"].browse(employee_id)
                values = {}
                values['shift_type'] = 'days'

                if len(schedules) > 0:
                    for schedule in schedules:
                        values['hr_department'] = emp.department_id.id
                        values['hr_employee'] = employee_id
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
                else:
                    schedules = all_schedules.search([
                        ('work_day', '=', dates_btwn - relativedelta(days=2)),
                        ('hr_employee', '=', employee_id),
                    ])
                    s_work = datetime.combine(dates_btwn, time())
                    e_work = s_work + \
                        timedelta(hours=23, minutes=59, seconds=59)

                    for schedule in schedules:
                        values['hr_department'] = emp.department_id.id
                        values['hr_employee'] = employee_id
                        values['hr_employee_schedule'] = 0
                        values['hr_employee_shift'] = schedule.hr_employee_shift.id
                        values['hr_employee_shift_template'] = schedule.hr_employee_shift_template.id
                        values['hr_employee_shift_dayplan'] = schedule.hr_employee_shift_dayplan.id
                        values['shift_type'] = 'days'
                        values['work_day'] = dates_btwn
                        values['week_day'] = str(dates_btwn.weekday())
                        values['lunch_time_from'] = None
                        values['lunch_time_to'] = None
                        values['start_work'] = s_work
                        values['end_work'] = e_work

                if values['shift_type'] == 'shift':
                    date_from = datetime.combine(dates_btwn, time())
                    date_to = datetime.combine(dates_btwn, time())
                    date_to = date_to + \
                        timedelta(hours=23, minutes=59, seconds=59)
                else:
                    date_from = datetime.combine(dates_btwn, time())
                    date_from = date_from + \
                        timedelta(
                            seconds=setting_obj.start_work_date_from * 3600)
                    date_to = datetime.combine(dates_btwn, time())
                    date_to = date_to + \
                        timedelta(
                            seconds=setting_obj.start_work_date_to * 3600 + 59)

                attendances = self.env['hr.attendance'].search([
                    ('check_in', '>=', self._convert_datetime_field(date_from)),
                    ('check_in', '<=', self._convert_datetime_field(date_to)),
                    ('employee_id', '=', employee_id)
                ])

                if not attendances and values['shift_type'] == 'days':
                    date_from = datetime.combine(dates_btwn, time())
                    date_from = date_from + \
                        timedelta(
                            seconds=setting_obj.start_work_date_from * 3600)
                    date_to = datetime.combine(dates_btwn, time())
                    date_to = date_to + \
                        timedelta(
                            days=1) + timedelta(seconds=setting_obj.end_work_date_to * 3600 + 59)

                    attendances = self.env['hr.attendance'].search([
                        ('check_out', '>=', self._convert_datetime_field(date_from)),
                        ('check_out', '<=', self._convert_datetime_field(date_to)),
                        ('employee_id', '=', employee_id)
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

                req_id = []
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
                        if attendance_req.state == 'validate' or attendance_req.state == 'validate1':
                            req_id.append(attendance_req.id)
                    values['attendance_req_id'] = req_id

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
        ceo_approved_overtime = 0.0
        helper = [ceo_approved_overtime]
        if filters['calculate_type']:
            if filters['calculate_type'] == 'employee':
                employee_id = filters['employee_id']
                employee = self.env['hr.employee'].search(
                    [('id', '=', employee_id)], limit=1)
                domain = [('hr_employee', '=', employee.id), ('work_day',
                                                              '>=', start_date), ('work_day', '<=', end_date)]

                approved_overtimes = self.env['hr.leave'].sudo().search([
                    ('date_from', '>=', start_date),
                    ('date_to', '<=', end_date),
                    ('department_id', '=', employee.department_id.id),
                    ('holiday_status_id.overtime_type',
                     '=', 'total_allowed_overtime'),
                    ('state', 'in', ['validate', 'validate1'])
                ])
                for approved in approved_overtimes:
                    ceo_approved_overtime = approved.allowed_overtime_time
                    helper = [ceo_approved_overtime]

            else:
                department_id = filters['department_id']
                if type(department_id) is int:
                    dep = self.env['hr.department'].browse(department_id)
                else:
                    dep = department_id
                departments = self._get_departments(dep, [])
                parents = dep.ids[:]
                departments = departments + parents
                departments = list(dict.fromkeys(departments))
                domain = [('hr_department', '=', departments), ('work_day',
                                                                '>=', start_date), ('work_day', '<=', end_date)]
                approved_overtimes = self.env['hr.leave'].sudo().search([
                    ('date_from', '>=', start_date),
                    ('date_to', '<=', end_date),
                    ('department_id', 'in', [department_id]),
                    ('holiday_status_id.overtime_type',
                     '=', 'total_allowed_overtime'),
                    ('state', 'in', ['validate', 'validate1'])
                ], )

                for approved in approved_overtimes:
                    ceo_approved_overtime = approved.allowed_overtime_time
                    helper = [ceo_approved_overtime]

        else:
            domain = [('work_day', '>=', start_date),
                      ('work_day', '<=', end_date)]

        att_report_onj = self.env['hr.attendance.report']
        raw_data = att_report_onj.read_group(
            domain=domain,
            fields=[
                'hr_employee_shift',
                'work_days',
                'work_hours',
                'worked_days',
                'worked_hours',
                'formal_worked_hours',
                'overtime',
                'informal_overtime',
                'paid_req_time',
                'unpaid_req_time',
                'take_off_day',
                'difference_check_out',
                'difference_check_in',
                'ceo_approved_overtime:max',
                'overtime_holiday',
            ], groupby=['full_name', 'hr_department',
                        'hr_employee', 'register_id'],
            lazy=False
        )

        header = [
            ['full_name', 'Нэр овог'],
            ['register_id', 'Регистерийн дугаар'],
            ['work_days', 'Ажиллавал зохих'],
            ['work_hours', 'Цаг'],
            ['worked_days', 'Нийт ажилласан'],
            ['worked_hours', 'Цаг'],
            ['total_approved_time', 'Цалин бодогдох илүү цаг'],
            ['overtime_holiday', 'Баяр ёслолын өдөр ажилласан цаг'],  # 7
            ['total_confirmed_time', 'Батлагдсан илүү цаг'],
            ['total_informal_overtime', 'Нийт илүү цаг'],
            ['informal_overtime', 'Хуруу дарж авар илүү цаг'],
            ['overtime', 'Хүсэлтээр баталгаажсан илүү цаг'],
            ['total_absent_day', 'Нийт ажиллаагүй '],
            ['total_absent_hour', 'Цаг'],
            ['paid_req_time', 'Чөлөөтэй цаг '],
            ['unpaid_req_time', 'Цалингүй'],
            ['sick_time', 'Өвчтэй цаг'],
            ['', 'Э.Амралт  /өдөр/'],
            ['', 'Жирэмсний амралт /өдөр/'],
            ['take_off_day', 'Тасалсан өдөр'],
            ['difference_check_in', 'Хоцорсон цаг']
        ]

        data = {
            'data': raw_data,
            'header': header,
            'helper': helper
        }
        return data

    @api.model
    def get_attendances_report_total(self, filters):
        start_date = filters['start_date']
        end_date = filters['end_date']

        report_title_person = ''
        report_title_dep = ''
        report_title_position = ''

        report_title_parent = ''
        report_title_duration = ''
        report_title_dep = ''
        ceo_approved_overtime = 0.0

        if filters['calculate_type']:
            if filters['calculate_type'] == 'employee':
                employee_id = filters['employee_id']
                domain = [('hr_employee', '=', employee_id.id), ('work_day',
                                                                 '>=', start_date), ('work_day', '<=', end_date)]

                approved_overtimes = self.env['hr.leave'].sudo().search([
                    ('date_from', '>=', start_date),
                    ('date_to', '<=', end_date),
                    ('department_id', '=', employee_id.department_id.id),
                    ('holiday_status_id.overtime_type',
                     '=', 'total_allowed_overtime'),
                    ('state', 'in', ['validate', 'validate1'])
                ])
                for approved in approved_overtimes:
                    ceo_approved_overtime = approved.allowed_overtime_time

                report_title_person = employee_id.surname + \
                    ' ' + employee_id.name.upper() + ' (' + employee_id.pin + ')'
                report_title_dep = employee_id.department_id.name
                report_title_position = employee_id.job_id.name

                title = [
                    report_title_dep,
                    report_title_position,
                    report_title_person,
                    ceo_approved_overtime
                ]

            else:
                department_id = filters['department_id']
                if type(department_id) is int:
                    dep = self.env['hr.department'].browse(department_id)
                else:
                    dep = department_id
                departments = self._get_departments(dep, [])
                parents = dep.ids[:]
                departments = departments + parents
                departments = list(dict.fromkeys(departments))
                domain = [('hr_department', '=', departments), ('work_day',
                                                                '>=', start_date), ('work_day', '<=', end_date)]

                emp = self.env['hr.department'].search(
                    [('id', '=', department_id.id)], limit=1)
                if emp:
                    if emp.parent_id:
                        report_title_parent = emp.parent_id.name.upper()
                    report_title_dep = emp.name.upper()
                    report_title_duration = str(
                        start_date) + '  -  ' + str(end_date)

                approved_overtimes = self.env['hr.leave'].sudo().search([
                    ('date_from', '>=', start_date),
                    ('date_to', '<=', end_date),
                    ('department_id', 'in', [department_id.id]),
                    ('holiday_status_id.overtime_type',
                     '=', 'total_allowed_overtime'),
                    ('state', 'in', ['validate', 'validate1'])
                ], )

                for approved in approved_overtimes:
                    ceo_approved_overtime = approved.allowed_overtime_time

                title = [
                    report_title_parent,
                    report_title_dep,
                    report_title_duration,
                    ceo_approved_overtime
                ]

        else:
            domain = [('work_day', '>=', start_date),
                      ('work_day', '<=', end_date)]

        att_report_onj = self.env['hr.attendance.report']
        raw_data = att_report_onj.read_group(
            domain=domain,
            fields=[
                'hr_employee_shift',
                'work_days',
                'work_hours',
                'worked_days',
                'worked_hours',
                'formal_worked_hours',
                'overtime',
                'informal_overtime',
                'paid_req_time',
                'unpaid_req_time',
                'take_off_day',
                'difference_check_out',
                'difference_check_in',
                'ceo_approved_overtime:max',
                'overtime_holiday',
            ],
            groupby=['full_name', 'hr_department',
                     'hr_employee', 'register_id'],
            lazy=False
        )

        header = [
            ['full_name', 'Нэр овог'],
            ['register', 'Регистер'],
            ['hr_employee_shift', 'Ажиллах хуваарь'],
            ['work_days', 'Ажиллавал зохих өдөр'],
            ['work_hours', 'Ажиллавал зохих цаг'],
            ['worked_days', 'Ажилласан өдөр'],
            ['formal_worked_hours', 'Хуваарийн ажилласан цаг'],
            ['worked_hours', 'Нийт ажилласан цаг'],
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
            'type': 0,
            'title': title
        }

        return data

    @api.model
    def get_attendances_report_detail(self, filters):
        start_date = filters['start_date']
        end_date = filters['end_date']

        report_title_person = ''
        report_title_dep = ''
        report_title_position = ''
        report_title_parent = ''
        report_title_duration = ''

        if filters['calculate_type']:
            if filters['calculate_type'] == 'employee':
                employee_id = filters['employee_id']
                domain = [('hr_employee', '=', employee_id.id), ('work_day',
                                                                 '>=', start_date), ('work_day', '<=', end_date)]
                report_title_person = employee_id.surname + \
                    ' ' + employee_id.name.upper() + ' (' + employee_id.pin + ')'
                report_title_dep = employee_id.department_id.name
                report_title_position = employee_id.job_id.name
                title = [
                    report_title_dep,
                    report_title_position,
                    report_title_person,

                ]

            else:

                department_id = filters['department_id']
                if type(department_id) is int:
                    dep = self.env['hr.department'].browse(department_id)
                else:
                    dep = department_id
                departments = self._get_departments(dep, [])
                parents = dep.ids[:]
                departments = departments + parents
                departments = list(dict.fromkeys(departments))
                domain = [('hr_department', '=', departments), ('work_day',
                                                                '>=', start_date), ('work_day', '<=', end_date)]

                emp = self.env['hr.department'].search(
                    [('id', '=', department_id.id)], limit=1)
                if emp:
                    if emp.parent_id:
                        report_title_parent = emp.parent_id.name.upper()
                    report_title_dep = emp.name.upper()
                    report_title_duration = str(
                        start_date) + '  -  ' + str(end_date)

                title = [
                    report_title_parent,
                    report_title_dep,
                    report_title_duration,

                ]

        else:
            domain = [('work_day', '>=', start_date),
                      ('work_day', '<=', end_date)]

        att_report_obj = self.env['hr.attendance.report'].search(
            domain, order='full_name asc, work_day asc')
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
            'formal_worked_hours',
            'overtime',
            'informal_overtime',
            'paid_req_time',
            'unpaid_req_time',
            'take_off_day',
            'difference_check_out',
            'difference_check_in',
            'check_in',
            'check_out',
            'ceo_approved_overtime',
            'overtime_holiday'
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
            ['formal_worked_hours', 'Хуваарийн ажилласан цаг'],
            ['worked_hours', 'Нийт ажилласан цаг'],
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
            'type': 1,
            'title': title
        }
        return data

    @api.model
    def get_my_attendances_report(self, filters):
        row = []
        data = []
        header = [['field_name', 0]]
        employee_id = filters['employee_id']

        DATE_FORMAT = '%Y-%m-%d'
        start_date = datetime.strptime(
            filters['start_date'], DATE_FORMAT).date()
        end_date = datetime.strptime(filters['end_date'], DATE_FORMAT).date()
        dates_btwn = start_date
        while dates_btwn <= end_date:
            if dates_btwn.weekday() < 5:
                header.append([dates_btwn, 0])
            else:
                header.append([dates_btwn, 1])
            dates_btwn = dates_btwn + relativedelta(days=1)

        fields = [
            ['formal_worked_hours', 'Хуваарийн ажилласан цаг'],
            ['worked_hours', 'Ажилласан цаг'],
            ['check_in', 'Орсон'],
            ['check_out', 'Гарсан'],
            ['difference_check_out', 'Таслалт'],
            ['difference_check_in', 'Хоцролт']
        ]

        for f in fields:
            arr = {}
            arr['field_name'] = f[1]
            dates_btwn = start_date
            while dates_btwn <= end_date:
                att_report_obj = self.env['hr.attendance.report'].search(
                    [('hr_employee', '=', employee_id), ('work_day', '=', dates_btwn)])
                raw_data = att_report_obj.read([f[0]])
                arr[str(dates_btwn)] = raw_data
                dates_btwn = dates_btwn + relativedelta(days=1)
            row.append(arr)

        data.append({
            'data': row,
            'header': header,
            'fields': fields,
            'child_employees': {}
        })

        child_employees = self.env['hr.employee'].search(
            [('parent_id', '=', employee_id)])

        employee_att = []
        for index, employee in enumerate(child_employees, start=0):
            # if index > 2:
            #     break

            total_worked_hours = 0
            total_schedule_hours = 0
            new_row = []
            dates_btwn = start_date

            att_report_obj = self.env['hr.attendance.report'].search(
                [('hr_employee', '=', employee.id), ('work_day', '>=', start_date), ('work_day', '<=', end_date)])

            while dates_btwn <= end_date:
                raw_data = {}
                filtered_data = att_report_obj.filtered(
                    lambda r: r.work_day == dates_btwn)
                raw_data['check_in'] = filtered_data.read(['check_in'])
                raw_data['check_out'] = filtered_data.read(['check_out'])
                worked_hours = filtered_data.read(['worked_hours'])
                schedule_hours = filtered_data.read(['formal_worked_hours'])
                if len(worked_hours) > 0:
                    for worked_hour in worked_hours:
                        total_worked_hours += worked_hour['worked_hours']

                if len(schedule_hours) > 0:
                    for schedule_hour in schedule_hours:
                        total_schedule_hours += schedule_hour['formal_worked_hours']

                dates_btwn = dates_btwn + relativedelta(days=1)
                new_row.append(raw_data)

            employee_att.append({
                'employee_name': employee.name,
                'employee_attendances': new_row,
                'total_worked_hours': total_worked_hours,
                'total_schedule_hours': total_schedule_hours
            })

        data.append({
            'header': header,
            'data': {},
            'fields': {},
            'child_employees': employee_att
        })

        return data
