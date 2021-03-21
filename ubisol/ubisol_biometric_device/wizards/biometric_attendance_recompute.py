# -*- coding: utf-8 -*-

from odoo import models, fields, _
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class BiometricAttendanceRecompute(models.TransientModel):
    _name = 'biometric.attendance.wizard'
    _description = 'Biometric Attendance Wizard'

    start_date = fields.Date(string="Эхлэх хугацаа", required=True, default=(
        datetime.today()-relativedelta(months=+1)).strftime('%Y-%m-20'))
    end_date = fields.Date(string="Дуусах хугацаа", required=True,
                           default=datetime.now().strftime('%Y-%m-%d'))
    employee_id = fields.Many2many(
        'hr.employee', string="Employee", help="Employee")

    def action_compute(self):
        log_obj = self.env["log_file_import_wizard"].search([])

        for emp in self.employee_id:
            general_shift = self.env['hr.employee.schedule'].search(
                [('day_period', '!=', 3), ('hr_employee', '=', int(emp.id))], limit=1, order='id asc')
            setting_obj = self.env['hr.attendance.settings'].search(
                [], limit=1, order='id desc')

            start_date = datetime.combine(self.start_date, time())
            end_date = datetime.combine(self.end_date, time())

            [date_start_from_1, date_start_end_1, date_end_from_1, date_end_to_1, dt1,
                s_type] = log_obj._calculate_dates(emp, setting_obj, general_shift, start_date)
            [date_start_from_2, date_start_end_2, date_end_from_2, date_end_to_2, dt1,
                s_type] = log_obj._calculate_dates(emp, setting_obj, general_shift, end_date)

            date_from = date_start_from_1
            date_to = date_start_end_2

            attendances = self.env['hr.attendance'].search([
                ('check_in', '>=', date_from),
                ('check_in', '<=', date_to),
                ('employee_id', '=', emp.id)
            ]).unlink()

            attendances = self.env['hr.attendance'].search([
                ('check_out', '>=', date_from),
                ('check_out', '<=', date_to),
                ('employee_id', '=', emp.id)
            ]).unlink()

            date_from = date_end_from_1
            date_to = date_end_to_2

            attendances = self.env['hr.attendance'].search([
                ('check_in', '>=', date_from),
                ('check_in', '<=', date_to),
                ('employee_id', '=', emp.id)
            ]).unlink()

            attendances = self.env['hr.attendance'].search([
                ('check_out', '>=', date_from),
                ('check_out', '<=', date_to),
                ('employee_id', '=', emp.id)
            ]).unlink()

            biometrics = self.env["biometric.attendance"].search([
                ('punch_date_time', '>=', self.start_date),
                ('punch_date_time', '<=', self.end_date),
                ('pin_code', '=', emp.pin)
            ], order='punch_date_time asc')
            for b in biometrics:
                atten_time = b.punch_date_time
                prev_date = log_obj.checking_prev_att_within_thirty_sec(
                    emp, atten_time)

                if not prev_date:
                    continue

                status = log_obj.write_to_attendance(emp, atten_time)

                # att = self.env['hr.attendance'].search(
                #     [('employee_id', '=', emp.id), ('check_in', '=', atten_time)])
                # if not att:
                #     att = self.env['hr.attendance'].search(
                #         [('employee_id', '=', emp.id), ('check_out', '=', atten_time)])
                #     if not att:
                #         status = log_obj.write_to_attendance(emp, atten_time)

        action = {}
        return action
