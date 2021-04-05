# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, _
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

    cancel_user = fields.Many2many(
        'res.users', string="Ажилтан", help="Ажилтан")
    cancel_position = fields.Char(string='Товч утга', groups="base.group_user")
    cancel_comment = fields.Char(string='Товч утга', groups="base.group_user")

    def action_compute(self):
        ubi_letter = self.env["ubi.letter"].search([])
        active_ids = self.env.context.get('active_ids', [])
        cancel_letter = ubi_letter.cancel_sending(active_ids, self)
        action = self.env.ref('ubisol_letters.ubi_action_going_letter')
        if cancel_letter:
            raise RedirectWarning('Амжилттай буцаалаа.', action.id, _("Тийм"))

        return {}