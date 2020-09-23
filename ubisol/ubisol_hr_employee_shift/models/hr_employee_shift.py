# -*- coding: utf-8 -*-

import math
import pytz
import dateutil.parser
import datetime
import re
from odoo import models, fields, api
from datetime import datetime, timedelta
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

    def _convert_datetime_field(self, datetime_field, user=None):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        date_result = pytz.utc.localize(datetime_field).astimezone(local)
        seconds = date_result.utcoffset().total_seconds()
        date_result = date_result - timedelta(hours=seconds/1800)
        return datetime.strftime(date_result, '%Y-%m-%d %H:%M:%S')

    def _float_time_convert(self, float_val):    
        factor = float_val < 0 and -1 or 1    
        val = abs(float_val)
        return (factor * int(math.floor(val)), int(round((val % 1) * 60)))

    def _create_datetime(self, date_field, float_time_from, float_time_to):
        DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        if float_time_to <= float_time_from:
            float_time_to = float_time_to + 24
        hour_from, minute_from = self._float_time_convert(float_time_from)
        hour_to, minute_to = self._float_time_convert(float_time_to)
        datetime_field = datetime.strptime(str(date_field), DATETIME_FORMAT)
        datetime_field_from = datetime_field + timedelta(hours=hour_from,minutes=minute_from)
        datetime_field_to = datetime_field + timedelta(hours=hour_to,minutes=minute_to)
        datetime_field_from = self._convert_datetime_field(datetime_field_from)
        datetime_field_to = self._convert_datetime_field(datetime_field_to)
        return datetime_field_from, datetime_field_to

    def _find_week_day_index(self, week_day):
        week = { 
            'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6
        }
        return week.get(week_day, -1) 
    
    def _create_schedules(self, vals, shift):
        shift_template = self.env['resource.calendar'].browse(vals.get('resource_calendar_ids'))

        if shift_template.shift_type == 'days':
            day_ids = shift_template.normal_day_ids
        else:
            day_ids = shift_template.factory_day_ids
            total_len = len(day_ids) - 1
            counter = 0

        if vals.get('hr_department') == False:
            employees = self.env['hr.employee'].search([('id', '=', vals.get('hr_employee'))])
        else:
            employees = self.env['hr.employee'].search([('department_id', '=', vals.get('hr_department'))])

        DATE_FORMAT = '%Y-%m-%d'
        date_from = datetime.strptime(vals.get('date_from'), DATE_FORMAT)
        date_to = datetime.strptime(vals.get('date_to'), DATE_FORMAT)
        dates_btwn = date_from

        while dates_btwn <= date_to:
            if shift_template.shift_type == 'days':
                week_index = self._find_week_day_index(dates_btwn.strftime("%A"))
                if week_index < 5:
                    inside_counter = 0
                    for day in day_ids:
                        if inside_counter == week_index:
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
                                schedule_dict['week_day'] = day.week_day
                                schedule_dict['lunch_time_from'], schedule_dict['lunch_time_to'] = self._create_datetime(dates_btwn, day.lunch_time_from, day.lunch_time_to)
                                schedule_dict['start_work'], schedule_dict['end_work'] = self._create_datetime(dates_btwn, day.start_work, day.end_work)
                                self.env['hr.employee.schedule'].create(schedule_dict)
                            break
                        inside_counter = inside_counter + 1
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
                            schedule_dict['day_period'] = day.day_period.id
                            schedule_dict['lunch_time_from'], schedule_dict['lunch_time_to'] = self._create_datetime(dates_btwn, day.lunch_time_from, day.lunch_time_to)
                            schedule_dict['start_work'], schedule_dict['end_work'] = self._create_datetime(dates_btwn, day.start_work, day.end_work)
                            self.env['hr.employee.schedule'].create(schedule_dict)
                            counter = counter + 1
                        break
                    inside_counter = inside_counter + 1
                if counter > total_len:
                    counter = 0
            dates_btwn = dates_btwn + relativedelta(days=1) 

    @api.model
    def create(self, vals):
        shift = super(HrEmployeeShift, self).create(vals)

        self._create_schedules(vals, shift)

        return shift

    def write(self, vals):
        shift = super(HrEmployeeShift, self).write(vals)
        self.env['hr.employee.schedule'].search([('hr_employee_shift', '=', self.id)]).unlink()

        values = {}
        if "hr_department" in vals:
            values['hr_department'] = vals.get('hr_department')
        else:
            values['hr_department'] = self.hr_department.id
        if "hr_employee" in vals:
            values['hr_employee'] = vals.get('hr_employee')
        else:
            values['hr_employee'] = self.hr_employee.id
        if "resource_calendar_ids" in vals:
            values['resource_calendar_ids'] = vals.get('resource_calendar_ids')
        else:
            values['resource_calendar_ids'] = self.resource_calendar_ids.id
        if "date_from" in vals:
            values['date_from'] = vals.get('date_from')
        else:
            values['date_from'] = str(self.date_from)
        if "date_to" in vals:
            values['date_to'] = vals.get('date_to')
        else:
            values['date_to'] = str(self.date_to)

        print(values)
        self._create_schedules(values, self)

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
    lunch_time_from = fields.Datetime(string='Lunch time from', required=True)
    lunch_time_to = fields.Datetime(string='Lunch time to', required=True)
    start_work = fields.Datetime(string="Start Work", required=True, help="Start Work")
    end_work = fields.Datetime(string="End Work", required=True, help="End Work")