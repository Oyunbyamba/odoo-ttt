# -*- coding: utf-8 -*-

from odoo import models, fields


class CreateBankDefinition(models.TransientModel):
    _name = 'create.bank_definition'
    _description = 'Create Bank definition Wizard'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    organization_name = fields.Char(string="Organization Name")
    get_definition_date = fields.Date(string="Get definition Date")

    def print_report(self):
        data = {
            'model': 'create.bank_definition',
            'form': self.read()[0]
        }
        
        return self.env.ref('ubisol_hr_employee_upgrade.bank_definition_report_pdf').report_action(self, data=data)
