# -*- coding: utf-8 -*-

import pytz
from lxml import etree
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, time
from odoo.tools.safe_eval import safe_eval

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

    start_work_date = fields.Date(string="Start Work Date", compute="_compute_start_work_date", required=True, help="Start Work Date")
    end_work_date = fields.Date(string="End Work Date", compute="_compute_end_work_date", required=True, help="End Work Date")
    start_work_time = fields.Float(string="Start Work Time", compute="_compute_start_work_time", required=True, help="Start Work Time")
    end_work_time = fields.Float(string="End Work Time", compute="_compute_end_work_time", required=True, help="End Work Time")

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

    @api.depends("start_work")
    def _compute_start_work_date(self):
        for record in self:
            if record.start_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(record.start_work).astimezone(local)
                record.start_work_date = date_result

    @api.depends("end_work")
    def _compute_end_work_date(self):
        for record in self:
            if record.end_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(record.end_work).astimezone(local)
                record.end_work_date = date_result

    @api.depends("start_work")
    def _compute_start_work_time(self):
        for record in self:
            if record.start_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(record.start_work).astimezone(local)
                hour = date_result.hour
                minute = date_result.minute
                record.start_work_time = hour + minute/60

    @api.depends("end_work")
    def _compute_end_work_time(self):
        for record in self:
            if record.end_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(record.end_work).astimezone(local)
                hour = date_result.hour
                minute = date_result.minute
                record.end_work_time = hour + minute/60

    @api.model
    def get_departments(self):
        cr = self._cr
        cr.execute("""select * from hr_department group by hr_department.id""")
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][2], 'value': dat[i][0]})
        return data