# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.exceptions import UserError

class RecruitmentSource(models.Model):
    _inherit = 'hr.recruitment.source'



class Attachment(models.Model):
    _inherit = 'ir.attachment'