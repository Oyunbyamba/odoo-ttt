# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta

class MyAttendance(models.TransientModel):
    _name = 'my.attendance'
    _description = 'My Attendance Wizard'

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    start_date = fields.Date(string="Эхлэх хугацаа", required=True, default=(datetime.today()-relativedelta(months=+1)).strftime('%Y-%m-20'))
    end_date = fields.Date(string="Дуусах хугацаа", required=True, default=datetime.now().strftime('%Y-%m-%d'))
    employee_id = fields.Many2one('hr.employee', string="Ажилтан", help="Ажилтан", default=_get_employee_id, readonly=True, required=True)

    def my_attendance(self):
        start_date = datetime.combine(self.start_date, time())
        end_date = datetime.combine(self.end_date, time())
        end_date = end_date + timedelta(hours=23, minutes=59, seconds=59)
        employee_id = self.env.context.get('active_ids', [])
        domain = [('check_in', '>=', start_date), ('check_in', '<=', end_date), ('employee_id', '=', employee_id)]

        action = {
            "name": "Миний ирц",
            "type": "ir.actions.act_window",
            "res_model": "my.attendance",
            'domain': domain,
            "view_mode": "form",
            "target": "new",
        }

        return action
