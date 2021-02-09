# -*- coding: utf-8 -*-

from odoo import models, fields


class CreateDocumentOrder(models.TransientModel):
    _name = 'create.document_order'
    _description = 'Create Document Order Wizard'

    document_order = fields.Char(string="Баримтын дугаар")

    def print_report(self):
        employee_id = self.env.context.get('active_ids', [])
        data = {
            'model': 'create.document_order',
            'form': self.read()[0],
            'employee': employee_id[0]
        }        
        return self.env.ref('ubisol_hr_employee_upgrade.employee_working_report_pdf').report_action(self, data=data)
