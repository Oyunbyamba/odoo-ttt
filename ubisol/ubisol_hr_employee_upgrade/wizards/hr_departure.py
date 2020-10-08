# -*- coding: utf-8 -*-

from odoo import models, fields


class HrDeparture(models.TransientModel):
    _name = 'hr.departure.wizard'
    _inherit = 'hr.departure.wizard'

    departure_reason = fields.Selection(selection_add=[('other', 'Other')])
