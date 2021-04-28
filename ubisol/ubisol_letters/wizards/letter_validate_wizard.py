# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)


class LetterValidate(models.TransientModel):
    _name = 'letter.validate.wizard'
    _description = 'Letter Validate Wizard'

    comment = fields.Char(string='Тайлбар', groups="base.group_user")

    def action_validate(self):
        
        if self.env.context.get('active_id'):
            ubi_letter = self.env["ubi.letter.coming"].browse(self.env.context['active_id'])

            format_name = 'ubisol_letters.mail_act_letter_validate'
            user_name = self.env.user.employee_id.name if self.env.user.employee_id else self.env.user.name     
            note = _("%s дугаартай албан бичгийг 'Шийдвэрлэсэн' төлөвт '%s' орууллаа.") % (ubi_letter.letter_number, user_name) 
            ubi_letter.activity_schedule(format_name, note=note)
            ubi_letter.activity_feedback([format_name], feedback=self.comment)

            if ubi_letter.follow_id:
                going_letter = self.env['ubi.letter.going'].browse(ubi_letter.follow_id.id)
                going_letter.activity_schedule(format_name, note=note)
                going_letter.activity_feedback([format_name], feedback=self.comment)    

        return True