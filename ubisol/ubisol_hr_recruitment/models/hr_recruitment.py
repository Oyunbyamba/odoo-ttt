# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.exceptions import UserError

class RecruitmentSource(models.Model):
    _inherit = 'hr.recruitment.source'


class Applicant(models.Model):
    _inherit = 'hr.applicant'
    _order = 'name'

    @api.model
    def action_get_attachment_tree_view_inherit(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['context'] = {'default_res_model': self._name}
        action['domain'] = str([('res_model', '=', self._name)])
        action['search_view_id'] = (self.env.ref('hr_recruitment.ir_attachment_view_search_inherit_hr_recruitment').id, )
        return action

