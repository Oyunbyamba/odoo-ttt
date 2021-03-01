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
        title = data['title']

        row = 9

        if filters['calculate_type'] == 'employee':
            # header
            sheet.write(1, 9, 'ТАВАН ТОЛГОЙ ТҮЛШ ХХК', footer_format_bold)
            sheet.write(2, 8, 'ЦАГИЙН ТООЦООНЫ ХУУДАС /Ажилтнаар/',
                        footer_format_bold)
            sheet.write(3, 0, 'Алба,хэлтэс', header_footer_format)
            sheet.write(3, 1, title[0], footer_format_bold)
            sheet.write(
                3, 27, 'Сангийн сайдын 2017 оны 347 дугаар тушаалын хавсралт', header_right_format)
            sheet.write(4, 0, 'Албан тушаал', header_footer_format)
            sheet.write(4, 1, title[1], footer_format_bold)
            sheet.write(4, 27, 'НМаягт ЦХ-2', header_right_format)
            sheet.write(5, 0, 'Овог,нэр (ID) ', header_footer_format)
            sheet.write(5, 1, title[2], footer_format_bold)
            sheet.write(5, 27, 'Системээс таталт хийсэн огноо: ' +
                        datetime.today().strftime('%Y.%m.%d'), header_right_format)

        else:

            # header
            sheet.write(1, 9, 'ТАВАН ТОЛГОЙ ТҮЛШ ХХК', footer_format_bold)
            sheet.write(2, 8, 'ЦАГИЙН ТООЦООНЫ ХУУДАС /Алба, хэлтэсээр/',
                        footer_format_bold)
            sheet.write(3, 0, 'Алба', header_footer_format)
            sheet.write(3, 1, title[0], footer_format_bold)
            sheet.write(
                3, 27, 'Сангийн сайдын 2017 оны 347 дугаар тушаалын хавсралт', header_right_format)
            sheet.write(4, 0, 'Хэлтэс', header_footer_format)
            sheet.write(4, 1, title[1], footer_format_bold)
            sheet.write(4, 27, 'НМаягт ЦХ-2', header_right_format)
            sheet.write(5, 0, 'Хугацаа', header_footer_format)
            sheet.write(5, 1, title[2], footer_format_bold)
            sheet.write(5, 27, 'Системээс таталт хийсэн огноо: ' +
                        datetime.today().strftime('%Y.%m.%d'), header_right_format)

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
        sheet.write(8, 7, 'Баяр ёслолын өдөр ажилласан илүү цаг',
                    header_format)
        sheet.write(8, 10, 'Хуруу дарж авах илүү цаг', header_format)
        sheet.write(8, 11, 'Баяр ёслолын өдөр ажилласан илүү цаг',
                    header_format)
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
        total_confirmed_time = 0
        total_approved_time = 0
        total_overtime_all = 0
        i = 0
        while i < 28:
            sheet.write(9, i, i, header_format)
            i += 1
        row = 10
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
            approved_time = 0
            if title[3] >= l['informal_overtime']:
                confirmed_time = l['informal_overtime'] + l['overtime']
            else:
                confirmed_time = title[3] + l['overtime']

            sheet.write(row, 8, self._set_hour_format(
                confirmed_time), body_format)
            total_confirmed_time += confirmed_time

            approved_time = confirmed_time - l['difference_check_in']
            sheet.write(row, 6, self._set_hour_format(
                approved_time) or '', body_format)
            total_approved_time += approved_time

            total_overtime = l['informal_overtime'] + \
                l['overtime_holiday']+l['overtime']

            total_overtime_all += total_overtime

            sheet.write(row, 9, self._set_hour_format(
                total_overtime), body_format)
            sheet.write(row, 10, self._set_hour_format(
                l['informal_overtime']) or '', body_format)
            sheet.write(row, 11, self._set_hour_format(
                l['overtime_holiday']), body_format)
            sheet.write(row, 12, self._set_hour_format(
                l['overtime']) or '', body_format)
            sheet.write(row, 13, '', body_format)
            sheet.write(row, 14, '', body_format)
            sheet.write(row, 15, '', body_format)

            sheet.write(row, 16, self._set_hour_format(
                l['paid_req_time']) or '', body_format)
            sheet.write(row, 17, '', body_format)
            sheet.write(row, 18, self._set_hour_format(
                l['unpaid_req_time']) or '', body_format)

            sheet.write(row, 19, '', body_format)
            sheet.write(row, 20, '', body_format)
            sheet.write(row, 21, '', body_format)
            sheet.write(row, 22, '', body_format)
            sheet.write(row, 23, '', body_format)
            sheet.write(row, 24, '', body_format)

            sheet.write(row, 25, l['take_off_day']
                        or '', body_format)
            sheet.write(row, 26, self._set_hour_format(
                l['difference_check_out']), body_format)

            sheet.write(row, 27, self._set_hour_format(
                l['difference_check_in']), body_format)

            row += 1

        sheet.write(row, 0,  'Нийт', header_format)
        sheet.write(row, 1, '', body_format)
        sheet.write(row, 2, self._total_by_field(
            lines, 'work_days'), body_format)
        sheet.write(row, 3, self._set_hour_format(
            self._total_by_field(lines, 'work_hours')), body_format)
        sheet.write(row, 4, self._total_by_field(
            lines, 'worked_days'), body_format)
        sheet.write(row, 5, self._set_hour_format(
            self._total_by_field(lines, 'worked_hours')), body_format)
        sheet.write(row, 7, self._set_hour_format(
            self._total_by_field(lines, 'overtime_holiday')), body_format)

        sheet.write(row, 8, self._set_hour_format(
            total_confirmed_time), body_format)

        sheet.write(row, 6, self._set_hour_format(
            total_approved_time) or '', body_format)

        sheet.write(row, 9, self._set_hour_format(
            total_overtime_all), body_format)
        sheet.write(row, 10, self._set_hour_format(
            self._total_by_field(lines, 'informal_overtime')), body_format)
        sheet.write(row, 11, self._set_hour_format(
            self._total_by_field(lines, 'overtime_holiday')), body_format)
        sheet.write(row, 12, self._set_hour_format(
            self._total_by_field(lines, 'overtime')), body_format)
        sheet.write(row, 13, '', body_format)
        sheet.write(row, 14, '', body_format)
        sheet.write(row, 15, '', body_format)

        sheet.write(row, 16, self._set_hour_format(
            self._total_by_field(lines, 'paid_req_time')), body_format)
        sheet.write(row, 17, '', body_format)
        sheet.write(row, 18, self._set_hour_format(
            self._total_by_field(lines, 'unpaid_req_time')), body_format)

        sheet.write(row, 19, '', body_format)
        sheet.write(row, 20, '', body_format)
        sheet.write(row, 21, '', body_format)
        sheet.write(row, 22, '', body_format)
        sheet.write(row, 23, '', body_format)
        sheet.write(row, 24, '', body_format)

        sheet.write(row, 25, self._total_by_field(
            lines, 'take_off_day'), body_format)
        sheet.write(row, 26, self._set_hour_format(
            self._total_by_field(lines, 'difference_check_out')), body_format)

        sheet.write(row, 27, self._set_hour_format(
            self._total_by_field(lines, 'difference_check_in')), body_format)

        # last row
        row += 2

        sheet.write(
            row, 1, 'Тушаалаар баталгаажиж олговол зохих илүү цагийн хязгаар: ', header_footer_format)
        sheet.write(
            row, 6, title[3], header_footer_format)
        sheet.write(
            row, 12, 'Цагийн дээд хязгаартай байх /10-аас ихгүй гм/: ', header_footer_format)
        row += 2
        sheet.write(row, 1, 'Хянасан: ', footer_format_bold)
        sheet.write(row, 10, 'Шалгасан: ', footer_format_bold)
        row += 1
        sheet.write(row, 1, 'Төлөвлөлт, хөгжүүлэлтийн алба ',
                    header_footer_format)
        sheet.write(row, 10, 'Нягтлан бодогч: ', header_footer_format)
        row += 2
        sheet.write(row, 2, 'Дарга: ', header_footer_format)
        row += 2
        sheet.write(row, 1, 'Нийгмийн асуудал, хүний нөөцийн алба ',
                    header_footer_format)
        row += 2
        sheet.write(row, 2, 'Ахлах мэргэжилтэн: ', header_footer_format)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_xlsx_report(self, data, response):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        headers = data['header']
        lines = data['data']
        filters = data['filters']
        title = data['title']
        sheet = ''
        last_emp = 0
        for l in lines:

            if l['hr_employee'][0] != last_emp:
                sheet = workbook.add_worksheet(l['full_name'])
                # write column index
                sheet.set_row(0, 50)
                sheet.set_row(1, 15)
                sheet.set_row(2, 15)
                sheet.set_row(3, 15)
                sheet.set_row(4, 15)
                sheet.set_row(5, 15)
                sheet.set_row(6, 15)
                sheet.set_row(9, 15)
                sheet.set_row(10, 15)
                sheet.set_column(0, 13, 10)
                sheet.set_column(14, 27, 5)
                sheet.set_column(28, 28, 10)

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
                body_format = workbook.add_format({
                    'bold': 0,
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter',
                    'text_wrap': True
                })

                row = 9
                # header
                sheet.write(1, 9, 'ТАВАН ТОЛГОЙ ТҮЛШ ХХК', footer_format_bold)
                sheet.write(2, 8, 'ЦАГИЙН ТООЦООНЫ ХУУДАС /Ажилтнаар/',
                            footer_format_bold)
                sheet.write(3, 0, 'Алба,хэлтэс', header_footer_format)
                sheet.write(3, 1, title[0], footer_format_bold)
                sheet.write(
                    3, 28, 'Сангийн сайдын 2017 оны 347 дугаар тушаалын хавсралт', header_right_format)
                sheet.write(4, 0, 'Албан тушаал', header_footer_format)
                sheet.write(4, 1, title[1], footer_format_bold)
                sheet.write(4, 28, 'НМаягт ЦХ-2', header_right_format)
                sheet.write(5, 0, 'Овог,нэр (ID) ', header_footer_format)
                if filters['calculate_type'] == 'employee':
                    sheet.write(5, 1, title[2], footer_format_bold)

                else:
                    sheet.write(5, 1, l['full_name'], footer_format_bold)

                sheet.write(5, 28, 'Системээс таталт хийсэн огноо: ' +
                            datetime.today().strftime('%Y.%m.%d'), header_right_format)

                # write data (for column title)
                sheet.merge_range('A7:A9', 'Огноо', merge_format)
                sheet.merge_range('B7:C8', 'Ажиллавал зохих', merge_format)
                sheet.merge_range('D7:E8', 'Ажилласан', merge_format)
                sheet.merge_range('F7:G8', 'Цаг бүртгэл', merge_format)
                sheet.merge_range('H7:N7', 'Илүү цаг', merge_format)
                sheet.merge_range(
                    'H8:I8', 'Цалин бодогдох илүү цаг', merge_format)
                sheet.merge_range('J8:J9', 'Батлагдсан илүү цаг', merge_format)
                sheet.merge_range('K8:K9', 'Нийт илүү цаг', merge_format)
                sheet.merge_range('L8:N8', 'Үүнээс', merge_format)
                sheet.merge_range('O7:AB7', 'Ажиллаагүй', merge_format)
                sheet.merge_range('O8:P8', 'БҮГД', merge_format)
                sheet.merge_range('Q8:R8', 'Чөлөөтэй /цалинтай/', merge_format)
                sheet.merge_range('S8:T8', 'Чөлөөтэй /цалингүй/', merge_format)
                sheet.merge_range('U8:V8', 'Өвчтэй', merge_format)
                sheet.merge_range('W8:X8', 'Ээлжийн амралттай', merge_format)
                sheet.merge_range(
                    'Y8:Z8', 'Жирэмсэний амралттай', merge_format)
                sheet.merge_range('AA8:AB8', 'Тасалсан', merge_format)
                sheet.merge_range('AC7:AC9', 'Хоцорсон цаг', merge_format)
                sheet.write(8, 1, 'Өдөр', header_format)
                sheet.write(8, 2, 'Нийт цаг', header_format)
                sheet.write(8, 3, 'Өдөр', header_format)
                sheet.write(8, 4, 'Нийт цаг', header_format)
                sheet.write(8, 5, 'Ирсэн', header_format)
                sheet.write(8, 6, 'Явсан', header_format)
                sheet.write(8, 7, 'Илүү цаг', header_format)
                sheet.write(8, 8, 'Баяр ёслолын өдөр ажилласан илүү цаг',
                            header_format)
                sheet.write(8, 11, 'Хуруу дарж авах илүү цаг', header_format)
                sheet.write(8, 12, 'Баяр ёслолын өдөр ажилласан илүү цаг',
                            header_format)
                sheet.write(
                    8, 13, 'Хүсэлтээр баталгаажсан илүү цаг', header_format)
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
                sheet.write(8, 26, 'Өдөр', header_rotation_format)
                sheet.write(8, 27, 'Цаг', header_rotation_format)
                i = 0
                while i < 29:
                    sheet.write(row, i, i, header_format)
                    i += 1
                last_emp = l['hr_employee'][0]
                row = 10
            total_confirmed_time = 0.0

            sheet.write(row, 0, l['work_day'] or '', body_format)
            sheet.write(row, 1, l['work_days'] or '', body_format)
            sheet.write(row, 2, self._set_hour_format(
                l['work_hours']) or '', body_format)
            sheet.write(row, 3, l['worked_days'] or '', body_format)
            sheet.write(row, 4, self._set_hour_format(
                l['worked_hours']) or '', body_format)
            sheet.write(row, 5, self._set_check_format(
                l['check_in']), body_format)
            sheet.write(row, 6, self._set_check_format(
                l['check_out']), body_format)
            sheet.write(row, 8, self._set_hour_format(
                l['overtime_holiday']), body_format)

            confirmed_time = 0

            confirmed_time = l['informal_overtime'] + l['overtime']
            total_confirmed_time += confirmed_time
            sheet.write(row, 10, self._set_hour_format(
                confirmed_time), body_format)
            sheet.write(row, 11, self._set_hour_format(
                l['informal_overtime']) or '', body_format)
            sheet.write(row, 12, self._set_hour_format(
                l['overtime_holiday']), body_format)
            sheet.write(row, 14, self._set_hour_format(
                l['overtime']) or '', body_format)
            sheet.write(row, 17, self._set_hour_format(
                l['paid_req_time']) or '', body_format)
            sheet.write(row, 19, self._set_hour_format(
                l['unpaid_req_time']) or '', body_format)
            sheet.write(row, 20, '', body_format)
            sheet.write(row, 21, '', body_format)
            sheet.write(row, 22, '', body_format)
            sheet.write(row, 23, '', body_format)
            sheet.write(row, 24, '', body_format)
            sheet.write(row, 25, '', body_format)

            sheet.write(row, 26, l['take_off_day']
                        or '', body_format)
            sheet.write(row, 27, self._set_hour_format(
                l['difference_check_out']), body_format)

            sheet.write(row, 28, self._set_hour_format(
                l['difference_check_in']), body_format)

            row += 1

        sheet.write(row, 0, 'Нийт', header_format)
        sheet.write(row, 1, self._total_by_field(
            lines, 'work_days'), body_format)
        sheet.write(row, 2, self._set_hour_format(
            self._total_by_field(lines, 'work_hours')), body_format)
        sheet.write(row, 3, self._total_by_field(
            lines, 'worked_days'), body_format)
        sheet.write(row, 4, self._set_hour_format(
            self._total_by_field(lines, 'worked_hours')), body_format)
        sheet.write(row, 5, '', body_format)
        sheet.write(row, 6, '', body_format)
        sheet.write(row, 8, self._set_hour_format(
            self._total_by_field(lines, 'overtime_holiday')), body_format)

        sheet.write(row, 10, self._set_hour_format(
            total_confirmed_time), body_format)
        sheet.write(row, 11, self._set_hour_format(
            self._total_by_field(lines, 'informal_overtime')), body_format)
        sheet.write(row, 12, self._set_hour_format(
            self._total_by_field(lines, 'overtime_holiday')), body_format)
        sheet.write(row, 14, self._set_hour_format(
            self._total_by_field(lines, 'overtime')), body_format)
        sheet.write(row, 17, self._set_hour_format(
            self._total_by_field(lines, 'paid_req_time')), body_format)
        sheet.write(row, 19, self._set_hour_format(
            self._total_by_field(lines, 'unpaid_req_time')), body_format)
        sheet.write(row, 20, '', body_format)
        sheet.write(row, 21, '', body_format)
        sheet.write(row, 22, '', body_format)
        sheet.write(row, 23, '', body_format)
        sheet.write(row, 24, '', body_format)
        sheet.write(row, 25, '', body_format)

        sheet.write(row, 26, self._total_by_field(
            lines, 'take_off_day'), body_format)
        sheet.write(row, 27, self._set_hour_format(
            self._total_by_field(lines, 'difference_check_out')), body_format)

        sheet.write(row, 28, self._set_hour_format(
            self._total_by_field(lines, 'difference_check_in')), body_format)

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
        if val == False:
            return '-'

        DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
        time = datetime.strptime(val, DATE_FORMAT) + relativedelta(hours=8)
        time = time.time()
        time = time.strftime("%H:%M")
        return time

    @ api.model
    def _total_by_field(self, list, key):
        total = 0.0
        for l in list:
            if l[key]:
                total += float(l[key])
        return total
