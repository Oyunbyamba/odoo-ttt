# -*- coding: utf-8 -*-

from odoo import models, fields, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import json
import io
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class AttendanceReport(models.TransientModel):
    _name = 'attendance.report.wizard'
    _description = 'Attendance Report Wizard'

    calculate_type = fields.Selection([
        ('department', 'Хэлтэс'),
        ('employee', 'Ажилтан')
    ], string="Төрөл", default="department")
    start_date = fields.Date(string="Эхлэх хугацаа", required=True, default=(datetime.today()-relativedelta(months=+1)).strftime('%Y-%m-20'))
    end_date = fields.Date(string="Дуусах хугацаа", required=True, default=datetime.now().strftime('%Y-%m-%d'))
    employee_id = fields.Many2many('hr.employee', string="Employee", help="Employee")
    department_id = fields.Many2many('hr.department', string="Department", help="Department")

    def action_compute(self):
        reports = self.env["hr.attendance.report"].search([])
        [header, data] = reports.calculate_report(self.start_date, self.end_date, self.calculate_type, self.department_id, self.employee_id)
        
        action = {
          "name": "Ирцийн график",
          "type": "ir.actions.act_window",
          "res_model": "hr.attendance.report",
          "view_mode": "pivot",
        }
        return action

        data = {
            'data': data,
            'header': header,
        }

        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'attendance.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                     }
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()

        headers = data['header']
        lines = data['data']

        row = 1

        # write data (for column title)
        for i, h in enumerate(headers):
            sheet.write(row, i + 1, h)
        row += 1

        # Set data
        for l in lines:
            for i, h in enumerate(headers):
                try:
                    if l[h]:
                         sheet.write(row, i + 1, l[h])
                except KeyError:
                    sheet.write(row, i + 1, '')
            row += 1
        
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
