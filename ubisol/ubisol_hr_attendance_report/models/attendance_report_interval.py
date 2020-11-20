# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import json
import io
import math
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class AttendanceReport(models.TransientModel):
    _name = 'attendance.report.interval'
    _description = 'Attendance Report Interval'
    _rec_name = 'complete_name'

    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', store=True)
    calculate_type = fields.Selection([
        ('department', 'Хэлтэс'),
        ('employee', 'Ажилтан')
    ], string="Төрөл")
    start_date = fields.Date(string="Эхлэх хугацаа", required=True, default=(datetime.today()-relativedelta(months=+1)).strftime('%Y-%m-20'))
    end_date = fields.Date(string="Дуусах хугацаа", required=True, default=datetime.now().strftime('%Y-%m-%d'))
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    department_id = fields.Many2one('hr.department', string="Department", help="Department")

    @api.depends('start_date', 'end_date')
    def _compute_complete_name(self):
        for record in self:
            record.complete_name = 'Ирцийн график'

    @api.model
    def attendance_report_interval(self, val):
        pass

    @api.model
    def total_attendance_report_download(self, val):
        reports = self.env["hr.attendance.report"].search([])
        values = self.env["attendance.report.interval"].browse(val)
        filters = {}
        filters['start_date'] = (values.start_date)
        filters['end_date'] = (values.end_date)
        filters['calculate_type'] = (values.calculate_type)
        filters['department_id'] = (values.department_id)
        filters['employee_id'] = (values.employee_id)
        res = reports.get_attendances_report_total(filters)

        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'attendance.report.interval',
                     'options': json.dumps(res, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Negdsen tailan',
                     }
        }

    @api.model
    def attendance_report_download(self, val):
        reports = self.env["hr.attendance.report"].search([])
        values = self.env["attendance.report.interval"].browse(val)
        filters = {}
        filters['start_date'] = (values.start_date)
        filters['end_date'] = (values.end_date)
        filters['calculate_type'] = (values.calculate_type)
        filters['department_id'] = (values.department_id)
        filters['employee_id'] = (values.employee_id)
        res = reports.get_attendances_report_detail(filters)

        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'attendance.report.interval',
                     'options': json.dumps(res, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Delgerengui tailan',
                     }
        }

    def get_xlsx_total_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()

        sheet.set_row(0, 50)
        sheet.set_row(1, 30)
        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 12, 12)

        header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })
        border_format = workbook.add_format({
            'border': 1, 
            'text_wrap': True
        })
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })

        headers = data['header']
        lines = data['data']
        filters = data['filters']

        title = filters['start_date'] + '-аас ' + filters['end_date'] + '-ны хоорондох ирцийн мэдээлэл'

        sheet.merge_range('A1:M1', title, merge_format)

        row = 1

        # write data (for column title)
        for i, h in enumerate(headers):
            sheet.write(row, i, h[1], header_format)
        row += 1

        # Set data
        for l in lines:
            for i, h in enumerate(headers):
                index = h[0]
                try:
                    if l[index]:
                        if index == 'hr_employee_shift':
                            sheet.write(row, i, l[index][1], border_format)
                        elif index == 'worked_days' or index == 'take_off_day' or index == 'full_name' or index == 'work_day' or index == 'work_days':
                            sheet.write(row, i, l[index], border_format)
                        else:
                            sheet.write(row, i, self._set_hour_format(l[index]), border_format)
                    else:
                        if index == 'worked_days' or index == 'take_off_day':
                            sheet.write(row, i, 0, border_format)
                        else:
                            sheet.write(row, i, '00:00', border_format)
                except KeyError:
                    sheet.write(row, i, '', border_format)
            row += 1
        
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()

        sheet.set_row(0, 50)
        sheet.set_row(1, 30)
        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 15, 12)

        header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })
        border_format = workbook.add_format({
            'border': 1, 
            'text_wrap': True
        })
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })

        headers = data['header']
        lines = data['data']
        filters = data['filters']

        title = filters['start_date'] + '-аас ' + filters['end_date'] + '-ны хоорондох ирцийн мэдээлэл'

        sheet.merge_range('A1:P1', title, merge_format)

        row = 1

        # write data (for column title)
        for i, h in enumerate(headers):
            sheet.write(row, i, h[1], header_format)
        row += 1

        emp_first_row = 0
        emp_first_row_i = 0

        # Set data
        for l in lines:
            if emp_first_row == 0:
                emp_first_row = l['hr_employee'][0]
                emp_first_row_i = row + 1
            employee_id = l['hr_employee'][0]
            if emp_first_row != employee_id:
                sheet.merge_range('A'+str(emp_first_row_i)+':A'+str(row - 1), l['full_name'], merge_format)
                emp_first_row = l['hr_employee'][0]
                emp_first_row_i = row
            for i, h in enumerate(headers):
                index = h[0]
                try:
                    if l[index]:
                        if index == 'hr_employee_shift':
                            sheet.write(row, i, l[index][1], border_format)
                        elif index == 'worked_days' or index == 'take_off_day' or index == 'full_name' or index == 'work_day' or index == 'work_days':
                            sheet.write(row, i, l[index], border_format)
                        elif index == 'check_in' or index == 'check_out':
                            sheet.write(row, i, self._set_check_format(l[index]), border_format)
                        else:
                            sheet.write(row, i, self._set_hour_format(l[index]), border_format)
                    else:
                        if index == 'worked_days' or index == 'take_off_day':
                            sheet.write(row, i, 0, border_format)
                        else:
                            sheet.write(row, i, '00:00', border_format)
                except KeyError:
                    sheet.write(row, i, '', border_format)
            row += 1
        sheet.merge_range('A'+str(emp_first_row_i)+':A'+str(row), l['full_name'], merge_format)
        
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @api.model
    def _set_hour_format(self, val):
        result = '{0:02.0f}:{1:02.0f}'.format(*divmod(val * 60, 60))
        return result
    
    @api.model
    def _set_check_format(self, val):
        DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
        time = datetime.strptime(val, DATE_FORMAT) + relativedelta(hours=8)
        time = time.time()
        time = time.strftime("%H:%M")
        return time