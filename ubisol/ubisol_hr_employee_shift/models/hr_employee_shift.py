# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrEmployeeShift(models.Model):
    """Ээлжээр ажиллах мастер өгөгдөл хадгалах хүснэгт"""
    _name = 'hr.employee.shift'
    _description = 'hr.employee.shift'

    name = fields.Char()
    shift_type = fields.Selection([
        ('normal', 'Normal'),
        ('factory', 'Factory')
    ], default="normal", tracking=True)
    schedule_days = fields.Integer(string="Schedule Days", required=True, default=8, help="Schedule Days")
    hr_department = fields.Many2one('hr.department', string="Department", required=True, help="Department")
    day_ids = fields.One2many('hr.employee.shift.dayplan', 'shift_id', string='Day Plan', help='Day Plan')

    @api.depends('value')
    def _value_pc(self):
        for record in self:
            record.value2 = float(record.value) / 100


class HrEmployeeDayPlan(models.Model):
    """Ээлжээр ажиллах мастер өгөгдлийн тухайн өдрийн мэдээлэл хадгалах хүснэгт"""

    _name = 'hr.employee.shift.dayplan'
    _description = 'HR Employee Shift Day Plan'

    shift_id = fields.Many2one('hr.employee.shift', string="Shift", help='Shift', invisible=1)
    start_date = fields.Date(string="Start Date", tracking=True)
    end_date = fields.Date(string="End Date", tracking=True)
    work_type = fields.Selection([
        ('day', 'Day'),
        ('night', 'Night')
    ], default="day", tracking=True)