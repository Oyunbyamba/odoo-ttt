# -*- coding: utf-8 -*-

import pytz
import sys
from datetime import datetime
import logging
import binascii

from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    device_id = fields.Char(string='Biometric Device ID', help="Device Id")

    check_in = fields.Datetime(
        string="Check In", required=False)

    @api.constrains('check_in',  'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        # for attendance in self:

        #     dt = attendance.check_in
        #     d1 = datetime.strftime(dt, "%Y-%m-%d 00:00:00")
        #     d2 = datetime.strftime(dt, "%Y-%m-%d 23:59:59")
        #     shift_start = self.env['hr.employee.schedule'].search(
        #         [('hr_employee', '=', int(attendance.employee_id)), ('start_work', '>=', d1), ('start_work', '<=', d2)])
        #     shift_end = self.env['hr.employee.schedule'].search(
        #         [('hr_employee', '=', int(attendance.employee_id)), ('end_work', '>=', d1), ('end_work', '<=', d2)])

        #     if((not shift_end) and (not shift_start)):

        #         work_start = datetime.strptime(
        #             datetime.strftime(dt, "%Y-%m-%d  01:00:00"), "%Y-%m-%d %H:%M:%S")
        #         work_end = datetime.strptime(datetime.strftime(
        #             dt, "%Y-%m-%d 10:00:00"), "%Y-%m-%d %H:%M:%S")

        #         check_out = abs(dt - work_end).total_seconds()
        #         check_in = abs(dt - work_start).total_seconds()
        #         last_attendance_before_check_in = self.env['hr.attendance'].search([
        #                         ('employee_id', '=', attendance.employee_id.id),
        #                         ('check_in', '<=', attendance.check_in),
        #                         ('id', '!=', attendance.id),

        #         if(check_out < check_in):
        #             attendance.check_out=dt

        # # we take the latest attendance before our check_in time and check it doesn't overlap with ours
        # last_attendance_before_check_in = self.env['hr.attendance'].search([
        #     ('employee_id', '=', attendance.employee_id.id),
        #     ('check_in', '<=', attendance.check_in),
        #     ('id', '!=', attendance.id),
        # ], order='check_in desc', limit=1)
        # if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
        #     raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
        #         'empl_name': attendance.employee_id.name,
        #         'datetime': format_datetime(self.env, attendance.check_in, dt_format=False),
        #     })

        # if not attendance.check_out:
        #     # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
        #     no_check_out_attendances = self.env['hr.attendance'].search([
        #         ('employee_id', '=', attendance.employee_id.id),
        #         ('check_out', '=', False),
        #         ('id', '!=', attendance.id),
        #     ], order='check_in desc', limit=1)
        #     if no_check_out_attendances:
        #         raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
        #             'empl_name': attendance.employee_id.name,
        #             'datetime': format_datetime(self.env, no_check_out_attendances.check_in, dt_format=False),
        #         })
        # else:
        #     # we verify that the latest attendance with check_in time before our check_out time
        #     # is the same as the one before our check_in time computed before, otherwise it overlaps
        #     last_attendance_before_check_out = self.env['hr.attendance'].search([
        #         ('employee_id', '=', attendance.employee_id.id),
        #         ('check_in', '<', attendance.check_out),
        #         ('id', '!=', attendance.id),
        #     ], order='check_in desc', limit=1)
        # if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
        #     raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
        #         'empl_name': attendance.employee_id.name,
        #         'datetime': format_datetime(self.env, last_attendance_before_check_out.check_in, dt_format=False),
        #     })


class BiometricMachine(models.Model):
    _name = 'biometric.machine'

    name = fields.Char(string='Төхөөрөмжийн IP', required=True,
                       help="IP хаяг оруулна уу")
    desc = fields.Char(string='Нэр', required=True,
                       help="Төхөөрөмжинд нэр өгнө үү")
    port_no = fields.Integer(
        string='Port No', required=True, help="Give the Port number")

    def insert_attendance(self):
        print("test")

    def import_attendance(self):
        print("TEST")
