# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import json
import io
import math
import logging
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)

class AttendanceReport(models.TransientModel):
    _name = 'attendance.report.interval'
    _description = 'Attendance Report Interval'
    _rec_name = 'complete_name'

    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name', store=True)
    calculate_type = fields.Selection([
        ('department', 'Хэлтэс'),
        ('employee', 'Ажилтан')
    ], string="Төрөл")
    start_date = fields.Date(string="Эхлэх хугацаа", required=True, default=(
        datetime.today()-relativedelta(months=+1)).strftime('%Y-%m-20'))
    end_date = fields.Date(string="Дуусах хугацаа", required=True,
                           default=datetime.now().strftime('%Y-%m-%d'))
    employee_id = fields.Many2one(
        'hr.employee', string="Employee", help="Employee")
    department_id = fields.Many2one(
        'hr.department', string="Department", help="Department")

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
        sheet.set_row(1, 15)
        sheet.set_row(2, 15)
        sheet.set_row(3, 15)
        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 12, 10)
        sheet.set_column(13, 26, 5)
        sheet.set_column(27, 27, 10)

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
        header_rotation_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'rotation': '90'
        })
        footer_format = workbook.add_format({
            'bold': 0,
            'border': 0,
            'align': 'initial',
            'valign': 'vcenter',
            'text_wrap': False
        })
        footer_format_bold = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'initial',
            'valign': 'vcenter',
            'text_wrap': False
        })

        headers = data['header']
        lines = data['data']
        filters = data['filters']

        row = 4

        # write data (for column title)
        sheet.merge_range('A2:A4', 'Овог Нэр', merge_format)
        sheet.merge_range('B2:B4', 'Регистрийн дугаар', merge_format)
        sheet.merge_range('C2:D3', 'Ажиллавал зохих', merge_format)
        sheet.merge_range('E2:F3', 'Ажилласан', merge_format)
        sheet.merge_range('G2:M2', 'Илүү цаг', merge_format)
        sheet.merge_range('G3:H3', 'Цалин бодогдох илүү цаг', merge_format)
        sheet.merge_range('I3:I4', 'Батлагдсан илүү цаг', merge_format)
        sheet.merge_range('J3:J4', 'Нийт илүү цаг', merge_format)
        sheet.merge_range('K3:M3', 'Үүнээс', merge_format)
        sheet.merge_range('N2:AA2', 'Ажиллаагүй', merge_format)
        sheet.merge_range('N3:O3', 'БҮГД', merge_format)
        sheet.merge_range('P3:Q3', 'Чөлөөтэй /цалинтай/', merge_format)
        sheet.merge_range('R3:S3', 'Чөлөөтэй /цалингүй/', merge_format)
        sheet.merge_range('T3:U3', 'Өвчтэй', merge_format)
        sheet.merge_range('V3:W3', 'Ээлжийн амралттай', merge_format)
        sheet.merge_range('X3:Y3', 'Жирэмсэний амралттай', merge_format)
        sheet.merge_range('Z3:AA3', 'Тасалсан', merge_format)
        sheet.merge_range('AB2:AB4', 'Хоцорсон цаг', merge_format)
        sheet.write(3, 2, 'Өдөр', header_format)
        sheet.write(3, 3, 'Нийт цаг', header_format)
        sheet.write(3, 4, 'Өдөр', header_format)
        sheet.write(3, 5, 'Нийт цаг', header_format)
        sheet.write(3, 6, 'Илүү цаг', header_format)
        sheet.write(3, 7, 'Баяр ёслолын өдөр ажилласан илүү цаг', header_format)
        sheet.write(3, 10, 'Хуруу дарж авах илүү цаг', header_format)
        sheet.write(3, 11, 'Баяр ёслолын өдөр ажилласан илүү цаг', header_format)
        sheet.write(3, 12, 'Хүсэлтээр баталгаажсан илүү цаг', header_format)
        sheet.write(3, 13, 'Өдөр', header_rotation_format)
        sheet.write(3, 14, 'Цаг', header_rotation_format)
        sheet.write(3, 15, 'Өдөр', header_rotation_format)
        sheet.write(3, 16, 'Цаг', header_rotation_format)
        sheet.write(3, 17, 'Өдөр', header_rotation_format)
        sheet.write(3, 18, 'Цаг', header_rotation_format)
        sheet.write(3, 19, 'Өдөр', header_rotation_format)
        sheet.write(3, 20, 'Цаг', header_rotation_format)
        sheet.write(3, 21, 'Өдөр', header_rotation_format)
        sheet.write(3, 22, 'Цаг', header_rotation_format)
        sheet.write(3, 23, 'Өдөр', header_rotation_format)
        sheet.write(3, 24, 'Цаг', header_rotation_format)
        sheet.write(3, 25, 'Өдөр', header_rotation_format)
        sheet.write(3, 26, 'Цаг', header_rotation_format)

        # write column index
        i = 0
        while i < 28:
            sheet.write(4, i, i, header_format)
            i += 1

        # last row
        row += 1

        sheet.write(row, 1, 'Тушаалаар баталгаажиж олговол зохих илүү цагийн хязгаар: ', footer_format)
        sheet.write(row, 12, 'Цагийн дээд хязгаартай байх /10-аас ихгүй гм/: ', footer_format)
        row += 2
        sheet.write(row, 1, 'Хянасан: ', footer_format_bold)
        sheet.write(row, 10, 'Шалгасан: ', footer_format_bold)
        row += 1
        sheet.write(row, 1, 'Төлөвлөлт, хөгжүүлэлтийн алба ', footer_format)
        sheet.write(row, 10, 'Нягтлан бодогч: ', footer_format)
        row += 2
        sheet.write(row, 2, 'Дарга: ', footer_format)
        row += 2
        sheet.write(row, 1, 'Нийгмийн асуудал, хүний нөөцийн алба ', footer_format)
        row += 2
        sheet.write(row, 2, 'Ахлах мэргэжилтэн: ', footer_format)


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

        title = filters['start_date'] + '-аас ' + \
            filters['end_date'] + '-ны хоорондох ирцийн мэдээлэл'

        sheet.merge_range('A1:P1', title, merge_format)

        row = 1

        # write data (for column title)
        for i, h in enumerate(headers):
            sheet.write(row, i, h[1], header_format)
        row += 1

        full_name = ''
        emp_first_row = 0
        emp_first_row_i = 0
        total = {'full_name': '-', 'work_day': '-', 'check_in': '-', 'check_out': '-', 'work_days': 0.0, 'work_hours': 0.0, 'worked_days': 0.0, 'worked_hours': 0.0,
                 'formal_worked_hours': 0.0, 'overtime': 0.0, 'informal_overtime': 0.0, 'paid_req_time': 0.0, 'unpaid_req_time': 0.0, 'take_off_day': 0.0, 'difference_check_out': 0.0, 'difference_check_in': 0.0}

        # Set data
        for l in lines:
            if emp_first_row == 0:
                full_name = l['full_name']
                emp_first_row = l['hr_employee'][0]
                emp_first_row_i = row
            employee_id = l['hr_employee'][0]
            if emp_first_row != employee_id:
                row += 1
                for i, h in enumerate(headers):
                    index = h[0]
                    if index == 'full_name' or index == 'check_in' or index == 'check_out' or index == 'worked_days' or index == 'take_off_day' or index == 'work_day' or index == 'work_days':
                        sheet.write(row - 1, i, total[index], border_format)
                    else:
                        sheet.write(row - 1, i, self._set_hour_format(
                            total[index]), border_format)
                sheet.merge_range('A'+str(emp_first_row_i + 1) +
                                  ':A'+str(row), full_name, merge_format)
                full_name = l['full_name']
                emp_first_row = l['hr_employee'][0]
                emp_first_row_i = row
                total = {'full_name': '-', 'work_day': '-', 'check_in': '-', 'check_out': '-', 'work_days': 0.0, 'work_hours': 0.0, 'worked_days': 0.0, 'worked_hours': 0.0,
                         'formal_worked_hours': 0.0, 'overtime': 0.0, 'informal_overtime': 0.0, 'paid_req_time': 0.0, 'unpaid_req_time': 0.0, 'take_off_day': 0.0, 'difference_check_out': 0.0, 'difference_check_in': 0.0}
            for i, h in enumerate(headers):
                index = h[0]
                try:
                    if l[index]:
                        if index == 'work_days' or index == 'work_hours' or index == 'worked_days' or index == 'worked_hours' or index == 'formal_worked_hours' or index == 'overtime' or index == 'informal_overtime' or index == 'paid_req_time' or index == 'unpaid_req_time' or index == 'take_off_day' or index == 'difference_check_out' or index == 'difference_check_in':
                            total[index] += l[index]

                        if index == 'hr_employee_shift':
                            sheet.write(row, i, l[index][1], border_format)
                        elif index == 'worked_days' or index == 'take_off_day' or index == 'full_name' or index == 'work_day' or index == 'work_days':
                            sheet.write(row, i, l[index], border_format)
                        elif index == 'check_in' or index == 'check_out':
                            sheet.write(row, i, self._set_check_format(
                                l[index]), border_format)
                        else:
                            sheet.write(row, i, self._set_hour_format(
                                l[index]), border_format)
                    else:
                        if index == 'worked_days' or index == 'take_off_day' or index == 'work_days':
                            sheet.write(row, i, 0, border_format)
                        elif index == 'check_in' or index == 'check_out':
                            sheet.write(row, i, '-', border_format)
                        else:
                            sheet.write(row, i, '00:00', border_format)
                except KeyError:
                    sheet.write(row, i, '', border_format)
            row += 1
        for i, h in enumerate(headers):
            index = h[0]
            if index == 'full_name' or index == 'check_in' or index == 'check_out' or index == 'worked_days' or index == 'take_off_day' or index == 'work_day' or index == 'work_days':
                sheet.write(row - 1, i, total[index], border_format)
            else:
                sheet.write(row - 1, i, self._set_hour_format(
                    total[index]), border_format)
        sheet.merge_range('A'+str(emp_first_row_i + 1)+':A' +
                          str(row + 1), full_name, merge_format)

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
