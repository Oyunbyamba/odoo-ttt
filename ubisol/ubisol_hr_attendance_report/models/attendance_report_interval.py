# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class AttendanceReport(models.TransientModel):
    _name = 'attendance.report.interval'
    _description = 'Attendance Report Interval'
    _rec_name = 'complete_name'

    calculate_type = fields.Selection([
        ('department', 'Хэлтэс'),
        ('employee', 'Ажилтан')
    ], string="Төрөл")
    start_date = fields.Date(string="Эхлэх хугацаа", required=True, default=(datetime.today()-relativedelta(months=+1)).strftime('%Y-%m-20'))
    end_date = fields.Date(string="Дуусах хугацаа", required=True, default=datetime.now().strftime('%Y-%m-%d'))
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    department_id = fields.Many2one('hr.department', string="Department", help="Department")
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name')

    def _compute_complete_name(self):
        res = []
        for record in self:
            name = "%s-аас %s-ны хооронд" % (record.start_date, record.end_date)
            res += [(record.id, name)]
        return res

    @api.model
    def attendance_report_interval(self, val):
        pass