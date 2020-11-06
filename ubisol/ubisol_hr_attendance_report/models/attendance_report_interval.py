# -*- coding: utf-8 -*-

from odoo import models, fields, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class AttendanceReport(models.TransientModel):
    _name = 'attendance.report.interval'
    _description = 'Attendance Report Interval'

    calculate_type = fields.Selection([
        ('department', 'Хэлтэс'),
        ('employee', 'Ажилтан')
    ], string="Төрөл", default="department")
    start_date = fields.Date(string="Эхлэх хугацаа", required=True, default=(datetime.today()-relativedelta(months=+1)).strftime('%Y-%m-20'))
    end_date = fields.Date(string="Дуусах хугацаа", required=True, default=datetime.now().strftime('%Y-%m-%d'))
    employee_id = fields.Many2many('hr.employee', string="Employee", help="Employee")
    department_id = fields.Many2many('hr.department', string="Department", help="Department")

