# -*- coding: utf-8 -*-

from odoo import models, fields


class CreateBankDefinition(models.TransientModel):
    _name = 'create.bank_definition'
    _description = 'Create Bank definition Wizard'

    manager_id = fields.Many2one('hr.employee', string="Definition Manager")
    # organization_name = fields.Char(string="Organization Name")
    # get_definition_date = fields.Date(string="Get definition Date")
    bank_name = fields.Many2one('res.bank', string="Bank name")

    def print_report(self):
        employee_id = self.env.context.get('active_ids', [])
        data = {
            'model': 'create.bank_definition',
            'form': self.read()[0],
            'employee': employee_id[0]
        }        
        return self.env.ref('ubisol_hr_employee_upgrade.bank_definition_report_pdf').report_action(self, data=data)
