# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class HrDepartureWizard(models.TransientModel):
    _name = 'hr.departure.wizard'
    _inherit = 'hr.departure.wizard'

    @api.model
    def default_get(self, fields):
        res = super(HrDepartureWizard, self).default_get(fields)
        if (not fields or 'employee_ids' in fields) and 'employee_ids' not in res:
            if self.env.context.get('active_ids'):
                res['employee_ids'] = [[6, False, self.env.context['active_ids']]]
                
        return res

    departure_reason = fields.Selection(selection_add=[('other', 'Бусад'), ('long_leave', 'Уртын чөлөө')])
    employee_id = fields.Many2one('hr.employee', string='Employee', required=False)
    employee_ids = fields.Many2many('hr.employee', string='Employee', required=True)

    def action_register_departure(self):
        employees = self.env['hr.employee'].browse(self.env.context.get('active_ids')) 
        for employee in employees:
            employee.departure_reason = self.departure_reason
            employee.departure_description = self.departure_description

        # if not employee.user_id.partner_id:
        #     return

        # for activity_type in self.plan_id.plan_activity_type_ids:
        #     self.env['mail.activity'].create({
        #         'res_id': employee.user_id.partner_id.id,
        #         'res_model_id': self.env['ir.model']._get('res.partner').id,
        #         'activity_type_id': activity_type.activity_type_id.id,
        #         'summary': activity_type.summary,
        #         'user_id': activity_type.get_responsible_id(employee).id,
        #     })