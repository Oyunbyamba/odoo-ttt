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
    employee_id = fields.Many2one('hr.employee')
    department_id = fields.Many2one('hr.department')
    start_work = fields.Datetime(string='Ажил эхлэх цаг')
    end_work = fields.Datetime(string='Ажил дуусах цаг')
    work_day = fields.Date(string='Ажлын өдөр')
    date_from = fields.Date(
        string="Start Work Date", compute="_compute_date_from", inverse='_set_date_from', help="Start Work Date")
    date_to = fields.Date(
        string="End Work Date", compute="_compute_date_to", inverse='_set_date_to', help="End Work Date")
    # start_work_time = fields.Float(
    #     string="Start Work Time", compute="_compute_start_work_time", help="Start Work Time")
    # end_work_time = fields.Float(
    #     string="End Work Time", compute="_compute_end_work_time", help="End Work Time")
    assign_type = fields.Selection(related='shift_id.assign_type', store=True)
    # name = fields.Char(related='shift_id.name')

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

    def _set_date_from(self):
        for record in self:
            record.date_from = record.date_from 

    def _set_date_to(self):
        for record in self:
            record.date_to = record.date_to      

    @api.depends('start_work')
    def _compute_date_from(self):
        for record in self:
            record.date_from = datetime.strftime(record.start_work, '%Y-%m-%d')

    @api.depends('end_work')
    def _compute_date_to(self):
        for record in self:
            record.date_to = datetime.strftime(record.end_work, '%Y-%m-%d')

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
        
        _logger.info(vals)
        _logger.info(vals.get('shift_id'))
        _logger.info(vals.get('shift_id').resource_calendar_ids)

        # workplans = self.env['hr.employee.workplan'].search([
        #     ('shift_id', '=', vals.get('shift_id')),
        #     ('work_day', '>=', vals.get('date_from')),
        #     ('work_day', '<=', vals.get('date_to')),
        # ])
        # _logger.info(workplans)

        # schedules = log_obj._create_schedules(vals, vals.get('shift_id'))
        # shift = super(HrEmployeeWorkplan, self).create(vals)

        return shift

    def write(self, vals):
        log_obj = self.env["hr.employee.shift"].search([])
        res = log_obj._check_duplicated_schedules(vals)
        
        _logger.info(vals)
        _logger.info(vals.get('shift_id'))
        _logger.info(vals.get('shift_id').resource_calendar_ids)

        # workplans = self.env['hr.employee.workplan'].search([
        #     ('shift_id', '=', vals.get('shift_id')),
        #     ('work_day', '>=', vals.get('date_from')),
        #     ('work_day', '<=', vals.get('date_to')),
        # ])
        # _logger.info(workplans)

        # schedules = log_obj._create_schedules(vals, vals.get('shift_id'))
        # shift = super(HrEmployeeWorkplan, self).create(vals)

        return shift

    def unlink(self):
        self.env['hr.employee.schedule'].search(
            [('workplan_id', '=', self.id)]).unlink()
        return super(HrEmployeeWorkplan, self).unlink()

