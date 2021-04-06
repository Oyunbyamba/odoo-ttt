# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import json
import io
from odoo.exceptions import ValidationError, AccessError, RedirectWarning
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)


class LetterReturn(models.TransientModel):
    _name = 'letter.return.wizard'
    _description = 'Letter Return Wizard'

    cancel_employee = fields.Many2one(
        'hr.employee', string="Ажилтан", help="Ажилтан")
    cancel_position = fields.Char(string='Товч утга', compute='_compute_employee_job', groups="base.group_user")
    cancel_comment = fields.Char(string='Товч утга', groups="base.group_user")

    @api.onchange('cancel_employee')
    def _compute_employee_job(self):
        if self.cancel_employee:
            self.cancel_position = self.cancel_employee.job_id.name

    def action_compute(self):
        ubi_letter = self.env["ubi.letter"].search([])
        if self.env.context.get('active_ids'):
            active_ids = self.env.context['active_ids']
            cancel_letter = ubi_letter.return_receiving(active_ids, self)
            action = self.env.ref('ubisol_letters.ubi_action_incoming_letter')
            # if cancel_letter:
                # raise RedirectWarning('Амжилттай буцаалаа.', action.id, _("Тийм"))

        return {}