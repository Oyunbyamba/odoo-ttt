# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResourceCalendarShift(models.Model):
    """Ээлжээр ажиллах мастер өгөгдөл хадгалах хүснэгт"""
    _inherit = 'resource.calendar'
    _description = 'hr employee shift template'

    shift_type = fields.Selection([
        ('days', 'Days'),
        ('shift', 'Shift')
    ], default="days", tracking=True)
    color = fields.Integer(string='Color Index', help="Color")
    factory_day_ids = fields.One2many('resource.calendar.shift', 'shift_id', string='Day Plan', help='Day Plan')
    normal_day_ids = fields.One2many('resource.calendar.shift', 'shift_id', 'Workings Time')


class HrEmployeeDayPlan(models.Model):
    """Ээлжээр ажиллах мастер өгөгдлийн тухайн өдрийн мэдээлэл хадгалах хүснэгт"""

    _name = 'resource.calendar.shift'
    _description = 'HR Employee Shift Day Plan'

    shift_id = fields.Many2one('resource.calendar', string="Shift", help='Shift', invisible=1, ondelete='cascade')

    name = fields.Char(required=True)
    week_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', required=True, index=True, default='0')
    day_period = fields.Many2one('resource.calendar.dayperiod', string="Day Period", help="Day Period of Work")

    lunch_time_from = fields.Float(string='Lunch time from', required=True)
    lunch_time_to = fields.Float(string='Lunch time to', required=True)

    start_work = fields.Float(string="Start Work", required=True, help="Start Work")
    end_work = fields.Float(string="End Work", required=True, help="End Work")

class HrEmployeeDayPeriod(models.Model):
    """Ээлжийн төлөв хадгалах хүснэгт"""

    _name = 'resource.calendar.dayperiod'

    name = fields.Char(string="Day Period")
