# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
        shift = super(HrEmployeeShift, self).create(vals)
        shift_template = self.env['resource.calendar'].browse(vals.get('resource_calendar_ids'))

        if shift_template.shift_type == 'days':
            day_ids = shift_template.normal_day_ids
        else:
            day_ids = shift_template.factory_day_ids
            total_len = len(day_ids)
            counter = 0

        if vals.get('hr_department') == False:
            employees = self.env['hr.employee'].search([('id', '=', vals.get('hr_employee'))])
        else:
            employees = self.env['hr.employee'].search([('department_id', '=', vals.get('hr_department'))])

        fmt = '%Y-%m-%d'
        date_from = datetime.strptime(vals.get('date_from'), fmt)
        date_to = datetime.strptime(vals.get('date_to'), fmt)
        dates_btwn = date_from

        while dates_btwn <= date_to:
            if shift_template.shift_type == 'days':
                pass
            else:
                inside_counter = 0
                for day in day_ids:
                    if inside_counter == counter:
                        for employee in employees:
                            schedule_dict = {}
                            schedule_dict['hr_department'] = vals.get('hr_department')
                            schedule_dict['hr_employee'] = employee.id
                            schedule_dict['date_from'] = vals.get('date_from')
                            schedule_dict['date_to'] = vals.get('date_to')
                            schedule_dict['work_day'] = dates_btwn.date()
                            schedule_dict['hr_employee_shift'] = shift.id
                            schedule_dict['hr_employee_shift_template'] = shift_template.id
                            schedule_dict['hr_employee_shift_dayplan'] = day.id
                            schedule_dict['shift_type'] = shift_template.shift_type
                            # schedule_dict['week_day'] = day.week_day
                            schedule_dict['day_period'] = day.day_period.id
                            schedule_dict['lunch_time_from'] = day.lunch_time_from
                            schedule_dict['lunch_time_to'] = day.lunch_time_to
                            schedule_dict['start_work'] = day.start_work
                            schedule_dict['end_work'] = day.end_work
                            schedule = self.env['hr.employee.schedule'].create(schedule_dict)
                            print(schedule)
                            counter = counter + 1
                        break
                    else:
                        inside_counter = inside_counter + 1
                if counter > total_len:
                    counter = 0
            dates_btwn = dates_btwn + relativedelta(days=1) 

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
    date_from = fields.Date(string='Starting Date')
    date_to = fields.Date(string='End Date')
    work_day = fields.Date(string='End Date')
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
    lunch_time_from = fields.Float(string='Lunch time from', required=True)
    lunch_time_to = fields.Float(string='Lunch time to', required=True)
    start_work = fields.Float(string="Start Work", required=True, help="Start Work")
    end_work = fields.Float(string="End Work", required=True, help="End Work")