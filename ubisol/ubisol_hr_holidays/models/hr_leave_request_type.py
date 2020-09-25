# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models


class UbisolHolidaysType(models.Model):
    _inherit = 'hr.leave.type' 
    _description = "Leave type"
   
    vacation = fields.Boolean('Ээлжийн амралт', default=False)
    one_step_days = fields.Integer('1 шатлалт чөлөөнд тооцох хоног', default=3)

