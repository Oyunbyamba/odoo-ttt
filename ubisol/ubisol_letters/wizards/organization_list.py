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

class OrganizationList(models.TransientModel):
    _name = 'organization.list.wizard'
    _description = 'Organization List Wizard'

    organization_name = fields.Char(string='Харилцагч байгууллагын нэр')
    organization_code = fields.Char(string='Харилцагч байгууллагын код')

    @api.model
    def create(self, vals):
        organization = super(OrganizationList, self).create(vals)

        return organization

    def choose_organization(self):
        if self.env.context.get('active_id'):
            
        return True    