# -*- coding: utf-8 -*-

import pytz
import sys
import datetime
import logging
import binascii

from odoo import models, fields, api


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    device_id = fields.Char(string='Biometric Device ID', help="Device Id")


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
