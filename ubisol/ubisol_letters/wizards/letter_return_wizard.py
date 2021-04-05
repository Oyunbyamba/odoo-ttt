# -*- coding: utf-8 -*-

from odoo import models, fields, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import json
import io
from odoo.exceptions import ValidationError
from odoo.tools import date_utils


class LetterReturn(models.TransientModel):
    _name = 'letter.return.wizard'
    _description = 'Letter Return Wizard'

    cancel_user = fields.Many2many(
        'res.users', string="Ажилтан", help="Ажилтан")
    cancel_position = fields.Char(string='Товч утга', groups="base.group_user")
    cancel_comment = fields.Char(string='Товч утга', groups="base.group_user")

    def action_compute(self):
        reports = self.env["hr.attendance.report"].search([])
        [header, data] = reports.calculate_report(
            self.start_date, self.end_date, self.calculate_type, self.department_id, self.employee_id)

        # action = {
        #   "name": "Ирцийн график",
        #   "type": "ir.actions.act_window",
        #   "res_model": "attendance.report.interval",
        #   "view_mode": "form,tree",
        #   "target": "new",
        # }
        action = {}
        return action
