# -*- coding: utf-8 -*-

# from odoo import models, fields, api

import pytz
import logging
from datetime import datetime, timedelta
from odoo import models, fields, _, api

_logger = logging.getLogger(__name__)

class HrEmployeeWorkplan(models.Model):
    _name = 'hr.employee.workplan'
    _rec_name = 'calendar_id'

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
    assign_type = fields.Selection(related='shift_id.assign_type', store=True)
    day_period = fields.Many2one(
        'resource.calendar.dayperiod', string="Day Period", help="Day Period of Work")
    shift_type = fields.Selection(related='calendar_id.shift_type')

    def _set_date_from(self):
        for record in self:
            record.date_from = record.date_from

    def _set_date_to(self):
        for record in self:
            record.date_to = record.date_to

    @api.depends('start_work')
    def _compute_date_from(self):
        for record in self:
            if record.start_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(
                    record.start_work).astimezone(local)
                record.date_from = date_result

    @api.depends('end_work')
    def _compute_date_to(self):
        for record in self:
            if record.end_work:
                user_tz = self.env.user.tz or pytz.utc
                local = pytz.timezone(user_tz)
                date_result = pytz.utc.localize(
                    record.end_work).astimezone(local)
                record.date_to = date_result

    @api.model
    def create(self, vals):
        workplan = super(HrEmployeeWorkplan, self).create(vals)

        return workplan

    def write(self, vals):
        for record in self:
            workplan = super(HrEmployeeWorkplan, self).write(vals)
            log_obj = self.env["hr.employee.shift"].search([])
 
            department_ids = record.shift_id.hr_department.read(['id'])
            departments = []
            for dep_id in department_ids:
                departments.append(dep_id['id'])    
            departments = [[6, False, departments]]

            ids = record.shift_id.hr_employee.read(['id'])
            employees = []
            for emp_id in ids:
                employees.append(emp_id['id'])
            employees = [[6, False, employees]]
            values = {
                'shift_id': record.shift_id,
                'resource_calendar_ids': record.calendar_id.id,
                'start_work': record.start_work,
                'end_work': record.end_work,
                'date_from': datetime.strftime(record.date_from, '%Y-%m-%d'),
                'date_to': datetime.strftime(record.date_to, '%Y-%m-%d'),
                'assign_type': record.assign_type,
                'hr_employee': employees,
                'hr_department': departments
            }
            res = log_obj._check_duplicated_schedules(values)

            workplans = self.env['hr.employee.workplan'].search([
                ('shift_id', '=', values.get('shift_id').id),
                ('work_day', '>=', values.get('date_from')),
                ('work_day', '<=', values.get('date_to'))
            ]).unlink()

            schedules = log_obj._create_schedules(values, values.get('shift_id'))

            return workplan

    # def unlink(self):
    #     self.env['hr.employee.workplan'].browse(
    #         [('id', '=', self.id)]).unlink()
    #     return super(HrEmployeeWorkplan, self).unlink()

