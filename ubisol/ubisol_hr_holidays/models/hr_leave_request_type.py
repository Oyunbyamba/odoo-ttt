# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models


class UbisolHolidaysType(models.Model):
    _inherit = 'hr.leave.type' 
    _description = "Leave type"
   

   
