# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrEmployeeSchedule(models.Model):
    """Хуваарилсан ээлж"""
    _name = 'hr.employee.schedule'
    _description = 'Hr Employee Schedule'
    _rec_name = 'hr_department'

    hr_department = fields.Many2one('hr.department', string="Department", help="Department")
    hr_employee = fields.Many2one('hr.employee', string="Employee", help="Employee")
    hr_employee_shift = fields.Many2one('hr.employee.shift', string="Employee Shift", help="Employee Shift")
    hr_employee_shift_template = fields.Many2one('resource.calendar', 'Employee Shift Template')
    hr_employee_shift_dayplan = fields.Many2one('resource.calendar.shift', 'Employee Shift Plan of Day')
    date_from = fields.Date(string='Starting Date')
    date_to = fields.Date(string='End Date')
    work_day = fields.Date(string='Work Day')
    is_main = fields.Boolean('Is Main', default=False)
    shift_type = fields.Selection([
        ('days', 'Days'),
        ('shift', 'Shift')
    ], default="shift", tracking=True)
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
    day_period_int = fields.Integer(string='Day Period Integer', help='Day Period of Work')
    lunch_time_from = fields.Datetime(string='Lunch time from', required=True)
    lunch_time_to = fields.Datetime(string='Lunch time to', required=True)
    start_work = fields.Datetime(string="Start Work", required=True, help="Start Work")
    end_work = fields.Datetime(string="End Work", required=True, help="End Work")

    @api.model
    def get_departments(self):
        cr = self._cr
        cr.execute("""select * from hr_department group by hr_department.id""")
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][2], 'value': dat[i][0]})
        return data