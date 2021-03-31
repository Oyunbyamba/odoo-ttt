# -*- coding: utf-8 -*-
import sys
import pytz
import base64
from datetime import datetime, timedelta
import logging
import binascii

from odoo import models, fields, api, http, exceptions, _
from odoo.tools import format_datetime
from zk import ZK, const

_logger = logging.getLogger(__name__)


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
    _inherit = ['mail.thread']

    name = fields.Char(string='Төхөөрөмжийн IP', required=True,
                       help="IP хаяг оруулна уу", tracking=True)
    desc = fields.Char(string='Нэр', required=True,
                       help="Төхөөрөмжинд нэр өгнө үү", tracking=True)
    port_no = fields.Integer(
        string='Port No', required=True, help="Give the Port number", tracking=True)

    active = fields.Boolean(
        string='Төхөөрөмж идэвхтэй эсэх', default=True,
        help="Уг төхөөрөмжийг ашиглахгүй бол сонгохгүй байна уу.")

    is_connected = fields.Boolean(
        string='Төхөөрөмжөөс автоматаар өгөгдөл татах эсэх', default=False,
        help="Төхөөрөмжөөс автоматаар өгөгдөл татах эсэх.")

    def download_all_attendance(self):
        devices = self.env['biometric.machine'].search(
            [('active', '=', True), ('is_connected', '=', True)])
        log_obj = self.env["log_file_import_wizard"].search([])

        last_id = self.env['biometric.attendance'].search(
            [], limit=1, order='id desc')
        if not last_id:
            last_id = 0
        else:
            last_id = last_id.id
        for device in devices:
            self.download_attendance_by_cron(device)

        new_attendances = self.env['biometric.attendance'].search(
            [('id', '>', last_id)], order='pin_code asc, punch_date_time asc')
        _logger.info(len(new_attendances))
        for attendance in new_attendances:

            get_user_id = self.env['hr.employee'].search(
                [('pin', '=', attendance.pin_code)], limit=1)
            if not get_user_id:
                _logger.info('USER Not FOUND')
                pass
            atten_time = attendance.punch_date_time
            prev_date = self.checking_prev_att_within_thirty_sec(
                get_user_id, atten_time)
            if not prev_date:
                pass
            log_obj.write_to_attendance(get_user_id, atten_time)

    def import_attendance(self, row, dev_id):

        if str(row[0]).strip() == '9999':
            return {}
        atten_time = row[1]
        atten_time = datetime.strptime(atten_time, '%Y-%m-%d %H:%M:%S')
        local_tz = pytz.timezone(self.env.user.tz or 'GMT')
        local_dt = local_tz.localize(atten_time, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
        atten_time = datetime.strptime(utc_dt, "%Y-%m-%d %H:%M:%S")

        duplicate_atten_ids = self.env['biometric.attendance'].search(
            [('pin_code', '=', str(row[0]).strip()), ('punch_date_time', '=', atten_time)])
        if duplicate_atten_ids:
            return {}
        else:
            _logger.info(atten_time)
            biometric = self.env['biometric.attendance'].create({'device_id': dev_id,
                                                                 'pin_code': str(row[0]).strip(),
                                                                 'punch_date_time': atten_time,
                                                                 'attendance_data': str(row[2]),
                                                                 'attendance_data1': str(row[3]),
                                                                 'attendance_data2': str(row[4]),
                                                                 'attendance_data3': str(row[5])})

        # prev_date = self.checking_prev_att_within_thirty_sec(
        #     get_user_id, atten_time)
        # if not prev_date:
        #     return {}

        # self.write_to_attendance(get_user_id, atten_time)

        return {}

    def download_attendance(self):

        for info in self:
            isIp = self.validIPAddress(info.name)
            attendances = []
            log_obj = self.env["log_file_import_wizard"].search([])
            if(isIp == 'IPv4'):
                conn = None
                zk = ZK(info.name, port=info.port_no, timeout=5)
                try:
                    print("Connecting to device ...")
                    conn = zk.connect()
                    print('Disabling device ...')
                    conn.disable_device()
                    print('Firmware Version: : {}'.format(
                        conn.get_firmware_version()))

                    attendances = conn.get_attendance()
                    for attendance in attendances:
                        _logger.info(attendance.timestamp.strftime(
                            "%Y-%m-%d %H:%M:%S"))
                        # row = [attendance.user_id, attendance.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        #        attendance.status, attendance.punch, 0, 0]

                        # self.import_attendance(row, info.id)

                    # log_obj.import_attendance(row, info.id)

                    # print('  User ID   : {}'.format(attendance.user_id))
                    # print('  timestamp   : {}'.format(attendance.timestamp))
                    # print('  status   : {}'.format(attendance.status))
                    # print('  punch   : {}'.format(attendance.punch))

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

    def download_attendance_by_cron(self, info):

        if info:
            isIp = self.validIPAddress(info.name)
            attendances = []
            log_obj = self.env["log_file_import_wizard"].search([])
            isError = False
            if(isIp == 'IPv4'):
                conn = None
                zk = ZK(info.name, port=info.port_no, timeout=5)
                try:
                    print("Connecting to device ...")
                    _logger.info(info.name)
                    conn = zk.connect()
                    print('Disabling device ...')
                    conn.disable_device()
                    print('Firmware Version: : {}'.format(
                        conn.get_firmware_version()))

                    attendances = conn.get_attendance()

                except:
                    isError = True
                if len(attendances) > 0:
                    _logger.info('TOTAL_ATT')
                    s_logger.info(len(attendances))
                    for attendance in attendances:
                        row = [attendance.user_id, attendance.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                               attendance.status, attendance.punch, 0, 0]
                        self.import_attendance(row, info.id)

                if conn:
                    conn.enable_device()
                    # if not isError:
                    # conn.clear_attendance()
                    conn.disconnect()
        return {}

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

    def checking_prev_att_within_thirty_sec(self, get_user_id, atten_time):
        prev_user = self.env['ir.config_parameter'].sudo(
        ).get_param('my.global.prev_user')
        prev_date = self.env['ir.config_parameter'].sudo(
        ).get_param('my.global.prev_date')

        if get_user_id:
            if not prev_user and not prev_date:
                prev_user = get_user_id.id
                prev_date = atten_time
                self.env['ir.config_parameter'].sudo().set_param(
                    'my.global.prev_user', prev_user)
                self.env['ir.config_parameter'].sudo().set_param(
                    'my.global.prev_date', prev_date)
            if int(prev_user) == int(get_user_id.id):
                if type(prev_date) is str:
                    prev_date = datetime.strptime(
                        prev_date, '%Y-%m-%d %H:%M:%S')
                if prev_date != atten_time:
                    diff = (atten_time - prev_date).total_seconds()
                    if abs(diff) <= 30:
                        return {}
                    else:
                        prev_user = get_user_id.id
                        prev_date = atten_time
                        self.env['ir.config_parameter'].sudo().set_param(
                            'my.global.prev_user', prev_user)
                        self.env['ir.config_parameter'].sudo().set_param(
                            'my.global.prev_date', prev_date)
                else:
                    prev_user = get_user_id.id
                    prev_date = atten_time
                    self.env['ir.config_parameter'].sudo().set_param(
                        'my.global.prev_user', prev_user)
                    self.env['ir.config_parameter'].sudo().set_param(
                        'my.global.prev_date', prev_date)
            elif prev_user != get_user_id.id:
                prev_user = get_user_id.id
                prev_date = atten_time
                self.env['ir.config_parameter'].sudo().set_param(
                    'my.global.prev_user', prev_user)
                self.env['ir.config_parameter'].sudo().set_param(
                    'my.global.prev_date', prev_date)
            return prev_date
        else:
            return {}
