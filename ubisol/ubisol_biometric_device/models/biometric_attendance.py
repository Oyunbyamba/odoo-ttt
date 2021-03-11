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
    fullname = fields.Char(compute="_compute_fullname", compute_sudo=True)
    department = fields.Char(compute="_compute_department", compute_sudo=True, search='_value_search')

    @api.depends("pin_code")
    def _compute_fullname(self):
        for record in self:
            pin_code = record.pin_code
            employee = self.env['hr.employee'].search(
                [('pin', '=', pin_code)], limit=1, order='id asc')
            if employee.surname:
                fullname = employee.surname[0] + '.' + employee.name
            else:
                fullname = employee.name
            record.fullname = fullname

    @api.depends("pin_code")
    def _compute_department(self):
        for record in self:
            pin_code = record.pin_code
            employee = self.env['hr.employee'].search(
                [('pin', '=', pin_code)], limit=1, order='id asc')

            if employee:
                record.department = employee.department_id.name
            else:
                record.department = ''    

    def _value_search(self, operator, value):
        recs = self.search([]).filtered(lambda x : x.department is True)
        if recs:
            return [('id', 'in', [x.id for x in recs])]            