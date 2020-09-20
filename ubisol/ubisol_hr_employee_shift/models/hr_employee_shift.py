# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrEmployeeShift(models.Model):
    """Ээлж хуваарилалт"""
    _name = 'hr.employee.shift'
    _description = 'HR Employee Shifts'

    name = fields.Char(required=True)
    assign_type = fields.Selection([
        ('department', 'Department'),
        ('employee', 'Employee')
    ], default="department", tracking=True)
    hr_department = fields.Many2one('hr.department', string="Department", help="Department")
    hr_employee = fields.Many2one('hr.employee', string="Employee", help="Employee")
    resource_calendar_ids = fields.Many2one('resource.calendar', 'Working Hours')