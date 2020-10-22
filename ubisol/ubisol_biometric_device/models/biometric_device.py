# -*- coding: utf-8 -*-

import pytz
import sys
from datetime import datetime
import logging
import binascii

from odoo import models, fields, api, http, exceptions, _
from odoo.tools import format_datetime
from zk import ZK, const


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    device_id = fields.Char(string='Biometric Device ID', help="Device Id")

    check_in = fields.Datetime(
        string="Check In", default=None, required=False)

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                delta = attendance.check_out - attendance.check_in
                attendance.worked_hours = delta.total_seconds() / 3600.0
            else:
                attendance.worked_hours = False

    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        """ verifies if check_in is earlier than check_out. """
        # for attendance in self:
        #     if attendance.check_in and attendance.check_out:
        #         if attendance.check_out < attendance.check_in:
        #             raise exceptions.ValidationError(
        #                 _('"Check Out" time cannot be earlier than "Check In" time.'))

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

    def test_connection(self):
        for info in self:
            isIp = self.validIPAddress(info.name)
            if(isIp == 'IPv4'):
                conn = None
                zk = ZK(info.name, port=info.port_no, timeout=5)
                try:
                    print("Connecting to device ...")
                    conn = zk.connect()
                except:
                    raise exceptions.ValidationError(
                        'IP хаяг буруу байна.')
                finally:
                    if conn:
                        conn.disconnect()
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Success'),
                                'message': _('Холболт амжилттай.'),
                                'sticky': False,
                            }
                        }
            else:
                raise exceptions.ValidationError(
                    'IP хаяг буруу байна.')

    def validIPAddress(self, IP):
        """
        :type IP: str
        :rtype: str
        """
        def isIPv4(s):
            try:
                return str(int(s)) == s and 0 <= int(s) <= 255
            except:
                return False

        def isIPv6(s):
            if len(s) > 4:
                return False
            try:
                return int(s, 16) >= 0 and s[0] != '-'
            except:
                return False
        if IP.count(".") == 3 and all(isIPv4(i) for i in IP.split(".")):
            return "IPv4"
        if IP.count(":") == 7 and all(isIPv6(i) for i in IP.split(":")):
            return "IPv6"
        return "Neither"
