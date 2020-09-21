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
    color = fields.Integer(string='Color Index', help="Color")
    hr_department = fields.Many2one('hr.department', string="Department", help="Department")
    hr_employee = fields.Many2one('hr.employee', string="Employee", help="Employee")
    date_from = fields.Date(string='Starting Date')
    date_to = fields.Date(string='End Date')
    resource_calendar_ids = fields.Many2one('resource.calendar', 'Working Hours')

    @api.model
    def create(self, vals):
        # {'assign_type': 'department', 'name': 'schedule 1', 'date_from': '2020-09-01', 'date_to': '2020-09-30', 
        # 'hr_department': 1, 'hr_employee': False, 'resource_calendar_ids': 6}
        shift = super(HrEmployeeShift, self).create(vals)
        return shift

    def write(self, vals):
        # employee = super(HrEmployee, self).write(vals)
        # contract_values = []
        # if self.contract_signed_date and self.create_contract:           
        #     contract_values.append({
        #         'name': self.name,
        #         'employee_id': self.id,
        #         'date_start': self.contract_signed_date,
        #         'department_id': self.department_id.id,
        #         'job_id': self.job_id.id,
        #         'wage': 0
        #     })
        #     self.env['hr.contract'].create(contract_values)
        # return employee
        shift = super(HrEmployeeShift, self).create(vals)
        return shift

class HrEmployeeSchedule(models.Model):
    """Хуваарилсан ээлж"""
    _name = 'hr.employee.schedule'
    _description = 'Hr Employee Schedule'

    hr_department = fields.Many2one('hr.department', string="Department", help="Department")
    hr_employee = fields.Many2one('hr.employee', string="Employee", help="Employee")
    hr_employee_shift = fields.Many2one('hr.employee.shift', string="Employee Shift", help="Employee Shift")
    hr_employee_shift_template = fields.Many2one('resource.calendar', 'Employee Shift Template')
    hr_employee_shift_dayplan = fields.Many2one('resource.calendar.shift', 'Employee Shift Plan of Day')
    shift_type = fields.Selection([
        ('days', 'Days'),
        ('shift', 'Shift')
    ], default="days", tracking=True)
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