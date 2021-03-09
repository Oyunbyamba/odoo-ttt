# -*- coding: utf-8 -*-

# from odoo import models, fields, api


from datetime import datetime, timedelta
from odoo import models, fields, _, api


class HrEmployeeWorkplan(models.Model):
    _name = 'hr.employee.workplan'
    _rec_name = 'employee_id'

    schedule_ids = fields.One2many(
        'hr.employee.schedule', 'workplan_id', string='Schedule', help='Schedule')
    employee_id = fields.Many2one('hr.employee')
    department_id = fields.Many2one('hr.department')
    pin = fields.Char(string="PIN")
<<<<<<< HEAD
    shift_id = fields.Many2one('hr.employee.shift', string='Ажлын төлөвлөгөө')
    calendar_id = fields.Many2one('resource.calendar', string='Ажлын хуваарийн загвар')
    employee_id = fields.Many2one('hr.employee')
    department_id = fields.Many2one('hr.department')
=======
    shift_id = fields.Many2one('hr.employee.shift')
    calendar_id = fields.Many2one('resource.calendar', 'Working Hours')
>>>>>>> parent of 9d981b2d (workplan)
    start_work = fields.Datetime(string='Ажил эхлэх цаг')
    end_work = fields.Datetime(string='Ажил дуусах цаг')
    assign_type = fields.Selection(related='shift_id.assign_type', store=True)

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

    def unlink(self):
        self.env['hr.employee.schedule'].search(
            [('workplan_id', '=', self.id)]).unlink()
        return super(HrEmployeeWorkplan, self).unlink()

# class HrEmployeeWork(models.Model):
#     _inherit = 'hr.employee'

#     shift_id = fields.Many2one('hr.employee.shift')
