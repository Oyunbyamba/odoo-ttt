# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class HrAttendanceInterval(models.TransientModel):
    _name = 'hr.attendance.interval'
    _description = 'Hr Attendance Interval'

    start_date = fields.Date(string="Эхлэх хугацаа", required=True, default=(datetime.today()-relativedelta(months=+1)).strftime('%Y-%m-20'))
    end_date = fields.Date(string="Дуусах хугацаа", required=True, default=datetime.now().strftime('%Y-%m-%d'))

    def _default_employee(self):
        return self.env.user.employee_id

    employee_id = fields.Many2one('hr.employee', string="Ажилтан", default=_default_employee, help="Employee")

    @api.model
    def attendance_report_interval(self, val):
        pass