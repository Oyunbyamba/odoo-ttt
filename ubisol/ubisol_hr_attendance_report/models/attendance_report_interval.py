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
        sheet.set_row(4, 15)
        sheet.set_row(5, 15)
        sheet.set_row(6, 15)
        sheet.set_row(9, 15)
        sheet.set_row(10, 15)
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
        header_footer_format = workbook.add_format({
            'bold': 0,
            'border': 0,
            'align': 'initial',
            'valign': 'vcenter',
            'text_wrap': False
        })
        header_right_format = workbook.add_format({
            'bold': 0,
            'border': 0,
            'align': 'right',
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

        body_format = workbook.add_format({
            'bold': 0,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })

        headers = data['header']
        lines = data['data']
        filters = data['filters']

        row = 9
        #header
        sheet.write(1, 9, 'ТАВАН ТОЛГОЙ ТҮЛШ ХХК', footer_format_bold)
        sheet.write(2, 8, 'ЦАГИЙН ТООЦООНЫ ХУУДАС /Алба, хэлтэсээр/', footer_format_bold)
        sheet.write(3, 0, 'Алба', header_footer_format)
        sheet.write(3, 1, 'ТӨЛӨВЛӨЛТ ХӨГЖҮҮЛЭЛТИЙН АЛБА', footer_format_bold)
        sheet.write(3, 27, 'Сангийн сайдын 2017 оны 347 дугаар тушаалын хавсралт', header_right_format)
        sheet.write(4, 0, 'Хэлтэс', header_footer_format)
        sheet.write(4, 1, 'МЭДЭЭЛЛИЙН ТЕХНОЛОГИЙН ХЭЛТЭС', footer_format_bold)
        sheet.write(4, 27, 'НМаягт ЦХ-2', header_right_format)
        sheet.write(5, 0, 'Хугацаа', header_footer_format)
        sheet.write(5, 27, 'Системээс таталт хийсэн огноо: '+datetime.today().strftime('%Y.%m.%d'), header_right_format)

        # write data (for column title)
        sheet.merge_range('A7:A9', 'Овог Нэр', merge_format)
        sheet.merge_range('B7:B9', 'Регистрийн дугаар', merge_format)
        sheet.merge_range('C7:D8', 'Ажиллавал зохих', merge_format)
        sheet.merge_range('E7:F9', 'Ажилласан', merge_format)
        sheet.merge_range('G7:M7', 'Илүү цаг', merge_format)
        sheet.merge_range('G8:H8', 'Цалин бодогдох илүү цаг', merge_format)
        sheet.merge_range('I8:I9', 'Батлагдсан илүү цаг', merge_format)
        sheet.merge_range('J8:J9', 'Нийт илүү цаг', merge_format)
        sheet.merge_range('K8:M8', 'Үүнээс', merge_format)
        sheet.merge_range('N7:AA7', 'Ажиллаагүй', merge_format)
        sheet.merge_range('N8:O8', 'БҮГД', merge_format)
        sheet.merge_range('P8:Q8', 'Чөлөөтэй /цалинтай/', merge_format)
        sheet.merge_range('R8:S8', 'Чөлөөтэй /цалингүй/', merge_format)
        sheet.merge_range('T8:U8', 'Өвчтэй', merge_format)
        sheet.merge_range('V8:W8', 'Ээлжийн амралттай', merge_format)
        sheet.merge_range('X8:Y8', 'Жирэмсэний амралттай', merge_format)
        sheet.merge_range('Z8:AA8', 'Тасалсан', merge_format)
        sheet.merge_range('AB7:AB9', 'Хоцорсон цаг', merge_format)
        sheet.write(8, 2, 'Өдөр', header_format)
        sheet.write(8, 3, 'Нийт цаг', header_format)
        sheet.write(8, 4, 'Өдөр', header_format)
        sheet.write(8, 5, 'Нийт цаг', header_format)
        sheet.write(8, 6, 'Илүү цаг', header_format)
        sheet.write(8, 7, 'Баяр ёслолын өдөр ажилласан илүү цаг', header_format)
        sheet.write(8, 10, 'Хуруу дарж авах илүү цаг', header_format)
        sheet.write(8, 11, 'Баяр ёслолын өдөр ажилласан илүү цаг', header_format)
        sheet.write(8, 12, 'Хүсэлтээр баталгаажсан илүү цаг', header_format)
        sheet.write(8, 13, 'Өдөр', header_rotation_format)
        sheet.write(8, 14, 'Цаг', header_rotation_format)
        sheet.write(8, 15, 'Өдөр', header_rotation_format)
        sheet.write(8, 16, 'Цаг', header_rotation_format)
        sheet.write(8, 17, 'Өдөр', header_rotation_format)
        sheet.write(8, 18, 'Цаг', header_rotation_format)
        sheet.write(8, 19, 'Өдөр', header_rotation_format)
        sheet.write(8, 20, 'Цаг', header_rotation_format)
        sheet.write(8, 21, 'Өдөр', header_rotation_format)
        sheet.write(8, 22, 'Цаг', header_rotation_format)
        sheet.write(8, 23, 'Өдөр', header_rotation_format)
        sheet.write(8, 24, 'Цаг', header_rotation_format)
        sheet.write(8, 25, 'Өдөр', header_rotation_format)
        sheet.write(8, 26, 'Цаг', header_rotation_format)

        # write column index
        i = 0
        while i < 28:
            sheet.write(9, i, i, header_format)
            i += 1
        row = 5
        for l in lines:
            sheet.write(row, 0, l['full_name'] or '', body_format)
            sheet.write(row, 1, l['register_id'] or '', body_format)
            sheet.write(row, 2, l['work_days'] or '', body_format)
            sheet.write(row, 3, self._set_hour_format(
                l['work_hours']) or '', body_format)
            sheet.write(row, 4, l['worked_days'] or '', body_format)
            sheet.write(row, 5, self._set_hour_format(
                l['worked_hours']) or '', body_format)
            sheet.write(row, 7, self._set_hour_format(
                l['overtime_holiday']), body_format)

            confirmed_time = 0
            if l['ceo_approved_overtime'] >= l['informal_overtime']:
                confirmed_time = l['informal_overtime'] + l['overtime']
            else:
                confirmed_time = l['ceo_approved_overtime'] + l['overtime']

            sheet.write(row, 8, self._set_hour_format(
                confirmed_time), body_format)
            sheet.write(row, 10, self._set_hour_format(
                l['informal_overtime']) or '', body_format)
            sheet.write(row, 11, self._set_hour_format(
                l['overtime_holiday']), body_format)
            sheet.write(row, 16, self._set_hour_format(
                l['paid_req_time']) or '', body_format)
            sheet.write(row, 18, self._set_hour_format(
                l['unpaid_req_time']) or '', body_format)

            sheet.write(row, 12, self._set_hour_format(
                l['overtime']) or '', body_format)

            sheet.write(row, 25, l['take_off_day']
                        or '', body_format)
            sheet.write(row, 26, l['difference_check_out']
                        or '', body_format)

            sheet.write(row, 27, l['difference_check_in'] or '', body_format)

            sheet.write(row, 9, '=TEXT(K'+str(row+1)+'+'+'L'+str(row+1) +
                        '+'+'M'+str(row+1)+',"h:mm")', body_format)

            row += 1

        # last row
        row += 2

        sheet.write(row, 1, 'Тушаалаар баталгаажиж олговол зохих илүү цагийн хязгаар: ', header_footer_format)
        sheet.write(row, 12, 'Цагийн дээд хязгаартай байх /10-аас ихгүй гм/: ', header_footer_format)
        row += 2
        sheet.write(row, 1, 'Хянасан: ', footer_format_bold)
        sheet.write(row, 10, 'Шалгасан: ', footer_format_bold)
        row += 1
        sheet.write(row, 1, 'Төлөвлөлт, хөгжүүлэлтийн алба ', header_footer_format)
        sheet.write(row, 10, 'Нягтлан бодогч: ', header_footer_format)
        row += 2
        sheet.write(row, 2, 'Дарга: ', header_footer_format)
        row += 2
        sheet.write(row, 1, 'Нийгмийн асуудал, хүний нөөцийн алба ', header_footer_format)
        row += 2
        sheet.write(row, 2, 'Ахлах мэргэжилтэн: ', header_footer_format)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()


        sheet.set_row(0, 50)
        sheet.set_row(1, 15)
        sheet.set_row(2, 15)
        sheet.set_row(3, 15)
        sheet.set_row(4, 15)
        sheet.set_row(5, 15)
        sheet.set_row(6, 15)
        sheet.set_row(9, 15)
        sheet.set_row(10, 15)
        sheet.set_column(0, 11, 10)
        sheet.set_column(12, 25, 5)
        sheet.set_column(26, 26, 10)

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
        header_footer_format = workbook.add_format({
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
        header_right_format = workbook.add_format({
            'bold': 0,
            'border': 0,
            'align': 'right',
            'valign': 'vcenter',
            'text_wrap': False
        })

        headers = data['header']
        lines = data['data']
        filters = data['filters']

        row = 9
        #header
        sheet.write(1, 9, 'ТАВАН ТОЛГОЙ ТҮЛШ ХХК', footer_format_bold)
        sheet.write(2, 8, 'ЦАГИЙН ТООЦООНЫ ХУУДАС /Ажилтнаар/', footer_format_bold)
        sheet.write(3, 0, 'Алба', header_footer_format)
        sheet.write(3, 1, 'ТӨЛӨВЛӨЛТ ХӨГЖҮҮЛЭЛТИЙН АЛБА', footer_format_bold)
        sheet.write(3, 26, 'Сангийн сайдын 2017 оны 347 дугаар тушаалын хавсралт', header_right_format)
        sheet.write(4, 0, 'Хэлтэс', header_footer_format)
        sheet.write(4, 1, 'МЭДЭЭЛЛИЙН ТЕХНОЛОГИЙН ХЭЛТЭС', footer_format_bold)
        sheet.write(4, 26, 'НМаягт ЦХ-2', header_right_format)
        sheet.write(5, 0, 'Хугацаа', header_footer_format)
        sheet.write(5, 26, 'Системээс таталт хийсэн огноо: '+datetime.today().strftime('%Y.%m.%d'), header_right_format)

        # write data (for column title)
        sheet.merge_range('A7:A9', 'Огноо', merge_format)
        sheet.merge_range('B7:C8', 'Ажиллавал зохих', merge_format)
        sheet.merge_range('D7:E8', 'Ажилласан', merge_format)
        sheet.merge_range('F7:L7', 'Илүү цаг', merge_format)
        sheet.merge_range('F8:G8', 'Цалин бодогдох илүү цаг', merge_format)
        sheet.merge_range('H8:H9', 'Батлагдсан илүү цаг', merge_format)
        sheet.merge_range('I8:I9', 'Нийт илүү цаг', merge_format)
        sheet.merge_range('J8:L8', 'Үүнээс', merge_format)
        sheet.merge_range('M7:Z7', 'Ажиллаагүй', merge_format)
        sheet.merge_range('M8:N8', 'БҮГД', merge_format)
        sheet.merge_range('O8:P8', 'Чөлөөтэй /цалинтай/', merge_format)
        sheet.merge_range('Q8:R8', 'Чөлөөтэй /цалингүй/', merge_format)
        sheet.merge_range('S8:T8', 'Өвчтэй', merge_format)
        sheet.merge_range('U8:V8', 'Ээлжийн амралттай', merge_format)
        sheet.merge_range('W8:X8', 'Жирэмсэний амралттай', merge_format)
        sheet.merge_range('Y8:Z8', 'Тасалсан', merge_format)
        sheet.merge_range('AA7:AA9', 'Хоцорсон цаг', merge_format)
        sheet.write(8, 1, 'Өдөр', header_format)
        sheet.write(8, 2, 'Нийт цаг', header_format)
        sheet.write(8, 3, 'Өдөр', header_format)
        sheet.write(8, 4, 'Нийт цаг', header_format)
        sheet.write(8, 5, 'Илүү цаг', header_format)
        sheet.write(8, 6, 'Баяр ёслолын өдөр ажилласан илүү цаг', header_format)
        sheet.write(8, 9, 'Хуруу дарж авах илүү цаг', header_format)
        sheet.write(8, 10, 'Баяр ёслолын өдөр ажилласан илүү цаг', header_format)
        sheet.write(8, 11, 'Хүсэлтээр баталгаажсан илүү цаг', header_format)
        sheet.write(8, 12, 'Өдөр', header_rotation_format)
        sheet.write(8, 13, 'Цаг', header_rotation_format)
        sheet.write(8, 14, 'Өдөр', header_rotation_format)
        sheet.write(8, 15, 'Цаг', header_rotation_format)
        sheet.write(8, 16, 'Өдөр', header_rotation_format)
        sheet.write(8, 17, 'Цаг', header_rotation_format)
        sheet.write(8, 18, 'Өдөр', header_rotation_format)
        sheet.write(8, 19, 'Цаг', header_rotation_format)
        sheet.write(8, 20, 'Өдөр', header_rotation_format)
        sheet.write(8, 21, 'Цаг', header_rotation_format)
        sheet.write(8, 22, 'Өдөр', header_rotation_format)
        sheet.write(8, 23, 'Цаг', header_rotation_format)
        sheet.write(8, 24, 'Өдөр', header_rotation_format)
        sheet.write(8, 25, 'Цаг', header_rotation_format)

        # write column index
        i = 0
        while i < 27:
            sheet.write(row, i, i, header_format)
            i += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    @ api.model
    def _set_hour_format(self, val):
        result = '{0:02.0f}:{1:02.0f}'.format(*divmod(val * 60, 60))
        return result

    @ api.model
    def _set_check_format(self, val):
        DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
        time = datetime.strptime(val, DATE_FORMAT) + relativedelta(hours=8)
        time = time.time()
        time = time.strftime("%H:%M")
        return time
