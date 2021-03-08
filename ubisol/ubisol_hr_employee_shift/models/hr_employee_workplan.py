# -*- coding: utf-8 -*-

# from odoo import models, fields, api

import pytz
import logging
from datetime import datetime, timedelta
from odoo import models, fields, _, api

_logger = logging.getLogger(__name__)

class HrEmployeeWorkplan(models.Model):
    _name = 'hr.employee.workplan'
    _rec_name = 'employee_id'

    schedule_ids = fields.One2many(
        'hr.employee.schedule', 'workplan_id', string='Schedule', help='Schedule')
    pin = fields.Char(string="PIN")
    shift_id = fields.Many2one('hr.employee.shift', string='Ажлын төлөвлөгөө')
    calendar_id = fields.Many2one('resource.calendar', string='Ажлын хуваарийн загвар')
    employee_id = fields.Many2one(related='shift_id.hr_employee')
    department_id = fields.Many2one(related='shift_id.hr_department')
    start_work = fields.Datetime(string='Ажил эхлэх цаг')
    end_work = fields.Datetime(string='Ажил дуусах цаг')
    start_work_date = fields.Date(
        string="Start Work Date", compute="_compute_start_work_date", inverse='_set_start_work_date', help="Start Work Date")
    end_work_date = fields.Date(
        string="End Work Date", compute="_compute_end_work_date", inverse='_set_end_work_date', help="End Work Date")
    start_work_time = fields.Float(
        string="Start Work Time", compute="_compute_start_work_time", help="Start Work Time")
    end_work_time = fields.Float(
        string="End Work Time", compute="_compute_end_work_time", help="End Work Time")

    date_from = fields.Date(compute='_compute_date_from', inverse='_set_date_from', compute_sudo=True)
    date_to = fields.Date(compute='_compute_date_to', inverse='_set_date_to', compute_sudo=True)
    assign_type = fields.Selection(related='shift_id.assign_type', store=True)
    name = fields.Char(related='shift_id.name')

    def emp_schedules(self):
        domain = [('hr_employee', '=', self.employee_id.id)]
        action = {
            "name": "Ажиллах график",
            "type": "ir.actions.act_window",
            "res_model": "hr.employee.schedule",
            'domain': domain,
            # 'context': {"search_default_employee": 1, "search_default_is_rest": 1},
            "view_mode": "timeline",
        }
        return action

    def _set_start_work_date(self):
        for record in self:
            record.start_work_date = record.start_work_date 

    def _set_end_work_date(self):
        for record in self:
            record.end_work_date = record.end_work_date      

    @api.depends('start_work')
    def _compute_start_work_date(self):
        for record in self:
            record.start_work_date = datetime.strftime(record.start_work_date, '%Y-%m-%d')

    @api.depends('end_work')
    def _compute_end_work_date(self):
        for record in self:
            record.end_work_date = datetime.strftime(record.end_work_date, '%Y-%m-%d')

    @api.depends("start_work")
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

    @api.depends("end_work")
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


    @api.model
    def create(self, vals):
        log_obj = self.env["hr.employee.shift"].search([])
        res = log_obj._check_duplicated_schedules(vals)
        
        self.env['hr.employee.workplan'].search(
            ['shift_id', '=', vals.get('shift_id')],
            ['start_work', '=', vals.get('shift_id')],
            )

        shift = super(HrEmployeeWorkplan, self).create(vals)

        self._create_schedules(vals, shift)

        return shift


    def unlink(self):
        self.env['hr.employee.schedule'].search(
            [('workplan_id', '=', self.id)]).unlink()
        return super(HrEmployeeWorkplan, self).unlink()

