# -*- coding: utf-8 -*-

import pytz
import logging
from lxml import etree
from odoo import models, fields, api
from datetime import datetime, timedelta, time

_logger = logging.getLogger(__name__)

class HrEmployeeSchedule(models.Model):
    """Хуваарилсан ээлж"""
    _name = 'hr.employee.schedule'
    _description = 'Hr Employee Schedule'
    _rec_name = 'hr_employee_shift_template'

    def _department_id_domain(self):
        return [('hr_department', '=', self.env.user.employee_id.department_id.id)]

    workplan_id = fields.Many2one(
        'hr.employee.workplan', string="Workplan", help="Workplan")
    hr_department = fields.Many2one(
        'hr.department', string="Department", domain=_department_id_domain, help="Department")
    hr_employee = fields.Many2one(
        'hr.employee', string="Employee", help="Employee")
    hr_employee_shift = fields.Many2one(
        'hr.employee.shift', string="Employee Shift", help="Employee Shift")
    hr_employee_shift_template = fields.Many2one(
        'resource.calendar', 'Employee Shift Template')
    hr_employee_shift_dayplan = fields.Many2one(
        'resource.calendar.shift', 'Employee Shift Plan of Day')
    date_from = fields.Date(string='Starting Date')
    date_to = fields.Date(string='End Date')
    work_day = fields.Date(string='Work Day')
    is_main = fields.Boolean('Is Main', default=False)
    shift_type = fields.Selection([
        ('days', 'Days'),
        ('shift', 'Shift')
    ], default="shift", tracking=True)
    week_day = fields.Selection([
        ('0', 'Даваа'),
        ('1', 'Мягмар'),
        ('2', 'Лхагва'),
        ('3', 'Пүрэв'),
        ('4', 'Баасан'),
        ('5', 'Бямба'),
        ('6', 'Ням')
    ], 'Day of Week', required=True, index=True, default='0')
    day_period = fields.Many2one(
        'resource.calendar.dayperiod', string="Day Period", help="Day Period of Work")
    day_period_int = fields.Integer(
        string='Day Period Integer', compute="_compute_day_period", help='Day Period of Work')
    lunch_time_from = fields.Datetime(string='Lunch time from')
    lunch_time_to = fields.Datetime(string='Lunch time to')
    start_work = fields.Datetime(
        string="Start Work", required=True, help="Start Work")
    end_work = fields.Datetime(
        string="End Work", required=True, help="End Work")

    start_work_date = fields.Date(
        string="Start Work Date", compute="_compute_start_work_date", help="Start Work Date")
    end_work_date = fields.Date(
        string="End Work Date", compute="_compute_end_work_date", help="End Work Date")
    start_work_time = fields.Float(
        string="Start Work Time", compute="_compute_start_work_time", help="Start Work Time")
    end_work_time = fields.Float(
        string="End Work Time", compute="_compute_end_work_time", help="End Work Time")
    shift_name = fields.Char(related='hr_employee_shift.name') 
    pin = fields.Char(related='hr_employee.pin')
    employee_name = fields.Char(related='hr_employee.name')
    start_time = fields.Char(compute="_compute_start_time")
    end_time = fields.Char(compute="_compute_end_time")
    period_type_name = fields.Char(string='Ээлж', compute='_compute_period_type_name')

    # @api.model
    # def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     result = super(HrEmployeeSchedule, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_type == 'tree':
    #         doc = etree.XML(result['arch'])
    #         for node in doc.xpath("//field[@name='hr_employee_shift']"):
    #             parent = node.getparent()
    #             xml_node_page = etree.Element('field', {'name': 'hr_department'})
    #             #You can insert the node here
    #             parent.insert(0, xml_node_page)
    #             # You can remove the node here
    #             # parent.remove(node)
    #             result['arch'] = etree.tostring(doc, encoding='unicode')
    #     return result

    # def _employee_id_domain(self):
    #     if self.user_has_groups('hr_holidays.group_hr_holidays_user') or self.user_has_groups('hr_holidays.group_hr_holidays_manager'):
    #         return []
    #     if self.user_has_groups('hr_holidays.group_hr_holidays_responsible'):
    #         return ['|', ('parent_id', '=', self.env.user.employee_id.id), ('user_id', '=', self.env.user.id)]
    #     return [('user_id', '=', self.env.user.id)]
    

    @api.onchange("start_work")
    def _compute_start_work_date(self):
        for record in self:
            if record.start_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(
                    record.start_work).astimezone(local)
                record.start_work_date = date_result

    @api.onchange("end_work")
    def _compute_end_work_date(self):
        for record in self:
            if record.end_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(
                    record.end_work).astimezone(local) 
                record.end_work_date = date_result

    @api.onchange("start_work")
    def _compute_start_work_time(self):
        for record in self:
            if record.start_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(
                    record.start_work).astimezone(local)
                hour = date_result.hour
                minute = date_result.minute
                record.start_work_time = hour + minute/60

    @api.onchange("end_work")
    def _compute_end_work_time(self):
        for record in self:
            if record.end_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(
                    record.end_work).astimezone(local)
                hour = date_result.hour
                minute = date_result.minute
                record.end_work_time = hour + minute/60  

    @api.depends("day_period", "shift_type")
    def _compute_day_period(self):
        for record in self:
            if record.shift_type and record.shift_type == "shift" and record.day_period:
                record.day_period_int = record.day_period.id
            else:
                record.day_period_int = None       

    @api.depends("start_work_time")
    def _compute_start_time(self):
        for record in self:
            record.start_time = self._set_hour_format(record.start_work_time)  

    @api.depends("end_work_time")
    def _compute_end_time(self):
        for record in self:
            record.end_time = self._set_hour_format(record.end_work_time)  

    @api.depends("week_day", "day_period")
    def _compute_period_type_name(self):
        for record in self:
            record.period_type_name = record.day_period.name
            if record.shift_type == 'days':
                record.period_type_name = dict(self._fields['week_day'].selection).get(record.week_day)

    @api.model
    def get_departments(self):
        cr = self._cr
        cr.execute("""select * from hr_department group by hr_department.id""")
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][2], 'value': dat[i][0]})
        return data


    @api.model
    def create(self, vals):
        schedule = super(HrEmployeeSchedule, self).create(vals)

        return schedule

    def write(self, vals):
        # schedule = super(HrEmployeeSchedule, self).write(vals)
        log_obj = self.env["hr.employee.shift"].search([])

        employees = []
        employees.append(self.hr_employee.id)
        employees = [[False, 0, employees]]
        start_time = ''
        end_time = ''

        resource_calendar_id = vals.get('hr_employee_shift_template') if vals.get('hr_employee_shift_template') else self.hr_employee_shift_template.id
        if vals.get('start_work'):
            date_from = datetime.strptime(vals.get('start_work'), '%Y-%m-%d %H:%M:%S')
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            date_result = pytz.utc.localize(date_from).astimezone(local)
            date_from = date_result.date() 
            hour = date_result.hour
            minute = date_result.minute
            start_time = hour + minute/60
        else:
            date_from = self.start_work_date

        if vals.get('end_work'):            
            date_to = datetime.strptime(vals.get('end_work'), '%Y-%m-%d %H:%M:%S')
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(user_tz)
            date_result = pytz.utc.localize(date_to).astimezone(local)
            date_to = date_result.date()
            hour = date_result.hour
            minute = date_result.minute
            end_time = hour + minute/60
        else:
            date_to = self.end_work_date   
        
        date_from = datetime.strftime(date_from, '%Y-%m-%d')
        date_to = datetime.strftime(date_to, '%Y-%m-%d')

        values = {
            'shift_id': self.hr_employee_shift,
            'resource_calendar_ids': resource_calendar_id,
            'start_time': start_time,
            'end_time': end_time,
            'date_from': date_from,
            'date_to': date_to,
            'assign_type': 'employee',
            'hr_employee': employees,
            'model_type': 'schedule'
        }

        prev_schedule = self.env['hr.employee.schedule'].search(
                [('id', '!=', self.id),
                ('hr_employee', '=', self.hr_employee.id), 
                ('work_day', '>=', date_from), 
                ('work_day', '<=', date_to)]).unlink()

        schedules = log_obj._create_schedules(values, values.get('shift_id'))
        if schedules:
            #Update self: with last schedule from new schedules. Then unlink new last schedule.
            schedule = super(HrEmployeeSchedule, self).write(schedules['schedule_dict'])
            schedules['schedule'].unlink()

        return True

    def _set_hour_format(self, val):
        result = '{0:02.0f}:{1:02.0f}'.format(*divmod(val * 60, 60))
        return result