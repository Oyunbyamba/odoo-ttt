# -*- coding: utf-8 -*-

import pytz
import sys
from datetime import datetime
import logging
import binascii

from odoo import models, fields, api, exceptions, _


class BiometricAttendance(models.Model):

    _name = 'biometric.attendance'

    pin_code = fields.Char(string='Pin Code')
    punch_date_time = fields.Datetime('DateTime ', required=False)
    device_id = fields.Many2one('biometric.machine', string='Төхөөрөмжийн нэр')
    attendance_data = fields.Char(string='Attendance data')
    attendance_data1 = fields.Char(string='Attendance data1')
    attendance_data2 = fields.Char(string='Attendance data2')
    attendance_data3 = fields.Char(string='Attendance data3')
