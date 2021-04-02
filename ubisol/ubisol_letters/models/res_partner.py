# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    @api.model
    def default_get(self, fields):
        res = super(ResPartner, self).default_get(fields)
        if (not fields or 'ubi_letter_org' in fields) and 'ubi_letter_org' in res:
            res['is_company'] = True
        return res

    ubi_letter_org = fields.Boolean('Харилцагч байгууллага мөн эсэх', default=False)
    ubi_letter_org_id = fields.Integer('Харилцагч байгууллагын код')

    @api.model
    def create(self, vals):
        res_partner = super(ResPartner, self).create(vals)

        return res_partner    
