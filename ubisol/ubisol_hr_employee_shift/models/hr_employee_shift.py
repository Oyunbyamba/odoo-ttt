# -*- coding: utf-8 -*-

import math
import pytz
import dateutil.parser
import re
import logging
from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

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
    hr_department = fields.Many2many(
        'hr.department', string="Department", help="Department")
    hr_employee = fields.Many2many(
        'hr.employee', string="Employee", help="Employee")
    date_from = fields.Date(string='Starting Date')
    date_to = fields.Date(string='End Date')
    resource_calendar_ids = fields.Many2one('resource.calendar', 'Хуваарийн загвар')
    pin = fields.Char(related='hr_employee.pin')
    department_name = fields.Char(related='hr_department.name')

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
        datetime_field_from = datetime_field + \
            timedelta(hours=hour_from, minutes=minute_from)
        datetime_field_to = datetime_field + \
            timedelta(hours=hour_to, minutes=minute_to)
        datetime_field_from = self._convert_datetime_field(datetime_field_from)
        datetime_field_to = self._convert_datetime_field(datetime_field_to)
        return datetime_field_from, datetime_field_to

    def shift_workplans(self):
        domain = [('shift_id', '=', self.id), '|', ('day_period.is_rest', '=', False), ('shift_type', '=', 'days')]
        action = {
            "name": "Ажиллах график",
            "type": "ir.actions.act_window",
            "res_model": "hr.employee.workplan",
            'domain': domain,
            # 'context': {"search_default_employee": 1, "search_default_is_rest": 1},
            "view_mode": "calendar",
        }
        return action    

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

    def _create_workplans(self, shift, day, work_day):
        work_dict = {}
        work_dict['shift_id'] = shift.id
        work_dict['calendar_id'] = shift.resource_calendar_ids.id
        work_dict['start_work'], work_dict['end_work'] = self._create_datetime(
                work_day, day.start_work, day.end_work)
        work_dict['assign_type'] = shift.assign_type       
        work_dict['work_day'] = work_day    
        if shift.resource_calendar_ids.shift_type == 'shift':
            work_dict['day_period'] = day.day_period.id
        workplan = self.env['hr.employee.workplan'].create(work_dict)

        return workplan

    def _create_schedules(self, vals, shift):
        _logger.info(vals)
        shift_template = self.env['resource.calendar'].browse(vals.get('resource_calendar_ids'))

        if shift_template.shift_type == 'days':
            day_ids = shift_template.normal_day_ids
        else:
            day_ids = shift_template.factory_day_ids
            total_len = len(day_ids) - 1
            counter = 0

        if vals.get('assign_type') == 'employee':
            employee_ids = vals.get('hr_employee')[0][2]
            employees = self.env['hr.employee'].search(
                [('id', 'in', employee_ids)])
        else:
            department_ids = vals.get('hr_department')[0][2]
            employees = self.env['hr.employee'].search(
                [('department_id', 'in', department_ids)])

        DATE_FORMAT = '%Y-%m-%d'
        date_from = datetime.strptime(vals.get('date_from'), DATE_FORMAT)
        date_to = datetime.strptime(vals.get('date_to'), DATE_FORMAT)
        dates_btwn = date_from

        while dates_btwn <= date_to:
            week_index = self._find_week_day_index(dates_btwn.strftime("%A"))
            if shift_template.shift_type == 'days':
                inside_counter = 0
                for day in day_ids:
                    if inside_counter == week_index:
                        if not vals.get('model_type'):
                            _logger.info(vals.get('model_type'))
                            workplan = self._create_workplans(shift, day, dates_btwn)
                        for index, employee in enumerate(employees):
                            schedule_dict = {}
                            schedule_dict['workplan_id'] = workplan.id
                            schedule_dict['hr_department'] = employee.department_id.id
                            schedule_dict['hr_employee'] = employee.id
                            schedule_dict['date_from'] = date_from
                            schedule_dict['date_to'] = date_to
                            schedule_dict['work_day'] = dates_btwn.date()
                            schedule_dict['hr_employee_shift'] = shift.id
                            schedule_dict['hr_employee_shift_template'] = shift_template.id
                            schedule_dict['hr_employee_shift_dayplan'] = day.id
                            schedule_dict['shift_type'] = shift_template.shift_type
                            schedule_dict['week_day'] = day.week_day
                            schedule_dict['lunch_time_from'], schedule_dict['lunch_time_to'] = self._create_datetime(
                                dates_btwn, day.lunch_time_from, day.lunch_time_to)
                            schedule_dict['start_work'], schedule_dict['end_work'] = self._create_datetime(
                                dates_btwn, day.start_work, day.end_work)
                            if index == 0:
                                schedule_dict['is_main'] = True
                            self.env['hr.employee.schedule'].create(
                                schedule_dict)
                        break
                    inside_counter = inside_counter + 1
            else:
                inside_counter = 0
                for day in day_ids:
                    if inside_counter == counter:
                        if not vals.get('model_type'):
                            _logger.info(vals.get('model_type'))
                            workplan = self._create_workplans(shift, day, dates_btwn)
                        for index, employee in enumerate(employees):
                            schedule_dict = {}
                            schedule_dict['workplan_id'] = workplan.id
                            schedule_dict['hr_department'] = employee.department_id.id
                            schedule_dict['hr_employee'] = employee.id
                            schedule_dict['date_from'] = date_from
                            schedule_dict['date_to'] = date_to
                            schedule_dict['work_day'] = dates_btwn.date()
                            schedule_dict['hr_employee_shift'] = shift.id
                            schedule_dict['hr_employee_shift_template'] = shift_template.id
                            schedule_dict['hr_employee_shift_dayplan'] = day.id
                            schedule_dict['shift_type'] = shift_template.shift_type
                            schedule_dict['day_period'] = day.day_period.id
                            schedule_dict['day_period_int'] = day.day_period.id

                            lunch_time_from = day.lunch_time_from
                            lunch_time_to = day.lunch_time_to
                            start_work = day.start_work
                            end_work = day.end_work

                            if week_index == 4:
                                if end_work < start_work:
                                    if shift_template.weekend_time_type == 'before':
                                        end_work = end_work - shift_template.weekend_time
                                    else:
                                        end_work = end_work + shift_template.weekend_time
                            elif week_index == 6:
                                if start_work > end_work:
                                    if shift_template.weekend_time_type == 'before':
                                        start_work = start_work - shift_template.weekend_time
                                    else:
                                        start_work = start_work + shift_template.weekend_time
                                else:
                                    if shift_template.weekend_time_type == 'before':
                                        lunch_time_from = lunch_time_from - shift_template.weekend_time
                                        lunch_time_to = lunch_time_to - shift_template.weekend_time
                                        start_work = start_work - shift_template.weekend_time
                                        end_work = end_work - shift_template.weekend_time
                                    else:
                                        lunch_time_from = lunch_time_from + shift_template.weekend_time
                                        lunch_time_to = lunch_time_to + shift_template.weekend_time
                                        start_work = start_work + shift_template.weekend_time
                                        end_work = end_work + shift_template.weekend_time
                            elif week_index == 5:
                                if shift_template.weekend_time_type == 'before':
                                    lunch_time_from = lunch_time_from - shift_template.weekend_time
                                    lunch_time_to = lunch_time_to - shift_template.weekend_time
                                    start_work = start_work - shift_template.weekend_time
                                    end_work = end_work - shift_template.weekend_time
                                else:
                                    lunch_time_from = lunch_time_from + shift_template.weekend_time
                                    lunch_time_to = lunch_time_to + shift_template.weekend_time
                                    start_work = start_work + shift_template.weekend_time
                                    end_work = end_work + shift_template.weekend_time

                            schedule_dict['lunch_time_from'], schedule_dict['lunch_time_to'] = self._create_datetime(
                                dates_btwn, lunch_time_from, lunch_time_to)
                            schedule_dict['start_work'], schedule_dict['end_work'] = self._create_datetime(
                                dates_btwn, start_work, end_work)

                            if index == 0:
                                schedule_dict['is_main'] = True
                            self.env['hr.employee.schedule'].create(schedule_dict)

                        counter = counter + 1
                        break
                    inside_counter = inside_counter + 1
                if counter > total_len:
                    counter = 0
            dates_btwn = dates_btwn + relativedelta(days=1)

    def _check_duplicated_schedules(self, vals):
        DATE_FORMAT = '%Y-%m-%d'
        if vals.get('date_from') and vals.get('date_to'):
            date_from = datetime.strptime(vals.get('date_from'), DATE_FORMAT)
            date_to = datetime.strptime(vals.get('date_to'), DATE_FORMAT)
            dates_btwn = date_from
            if vals.get('assign_type') == 'employee':
                employee_ids = vals.get('hr_employee')[0][2]
                employees = self.env['hr.employee'].search(
                    [('id', 'in', employee_ids)])
            else:
                department_ids = vals.get('hr_department')[0][2]
                employees = self.env['hr.employee'].search(
                    [('department_id', 'in', department_ids)])

            for employee in employees:
                prev_schedule = self.env['hr.employee.schedule'].search(
                    [('hr_employee', '=', employee.id), ('work_day', '>=', date_from.date()), ('work_day', '<=', date_to.date())]).unlink()

        return None

    @api.model
    def create(self, vals):
        res = self._check_duplicated_schedules(vals)
        if res:
            raise ValidationError(res.get('message'))

        # create shift for each department
        if vals.get('assign_type') == 'department':
            department_ids = vals.get('hr_department')[0][2]
            for dep_id in department_ids:
                vals['hr_department'] = [[6, False, [dep_id]]]
                shift = super(HrEmployeeShift, self).create(vals)
                self._create_schedules(vals, shift)
        else:
            shift = super(HrEmployeeShift, self).create(vals)
            self._create_schedules(vals, shift)

        return shift

    def write(self, vals):
        prev_date_to = self._origin.date_to
        shift = super(HrEmployeeShift, self).write(vals)

        values = {
            'name': self.name,
            'assign_type': self.assign_type,
            'resource_calendar_ids': self.resource_calendar_ids.id,
            'date_from': str(self.date_from),
            'date_to': str(self.date_to)
        }

        if vals.get('hr_department'):
            values['hr_department'] = vals.get('hr_department')
        else:
            dep_list = []
            department_ids = self.hr_department.read(['id'])
            for dep_id in department_ids:
                dep_list.append(dep_id['id'])    
            values['hr_department'] = [[6, False, dep_list]]

        if vals.get('hr_employee'):
            values['hr_employee'] = vals.get('hr_employee')
        else:
            emp_list = []
            employee_ids = self.hr_employee.read(['id'])
            for emp_id in employee_ids:
                emp_list.append(emp_id)    
            values['hr_employee'] = [[6, False, emp_list]]

        if vals.get('hr_department') or vals.get('hr_employee') or vals.get('resource_calendar_ids') or vals.get('date_from'):
            prev_workplans = self.env['hr.employee.workplan'].search([
                ('shift_id', '=', self.id), 
                ('work_day', '>=', values.get('date_from')), 
                ('work_day', '<=', values.get('date_to'))]).unlink()

            # if change departments: create shift for each department
            if self.assign_type == 'department':
                department_ids = self.hr_department.read(['id'])
                for index, dep in enumerate(department_ids):
                    values['hr_department'] = [[6, False, [dep['id']]]]
                    if index == 0:
                        super(HrEmployeeShift, self).write(values)
                        res = self._check_duplicated_schedules(values)
                        self._create_schedules(values, self)
                    else:    
                        new_shift = self.env['hr.employee.shift'].create(values)
            else:
                res = self._check_duplicated_schedules(values)
                self._create_schedules(values, self)        
        elif vals.get('date_to'):
            extend_date_from = datetime.strptime(str(prev_date_to), '%Y-%m-%d')
            extend_date_from = extend_date_from.date()+relativedelta(days=1)
            values['date_from'] = str(extend_date_from)

            prev_workplans = self.env['hr.employee.workplan'].search([
                ('shift_id', '=', self.id), 
                ('work_day', '>=', values.get('date_from')), 
                ('work_day', '<=', values.get('date_to'))]).unlink()

            res = self._check_duplicated_schedules(values)
            self._create_schedules(values, self)

        return shift

    def unlink(self):
        self.env['hr.employee.schedule'].search(
            [('hr_employee_shift', '=', self.id)]).unlink()
        self.env['hr.employee.workplan'].search(
            [('shift_id', '=', self.id)]).unlink()    
        return super(HrEmployeeShift, self).unlink()
