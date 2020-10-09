# -*- coding: utf-8 -*-

from odoo import models, fields


class PrintEmployeeDefinition(models.TransientModel):
    _name = 'print.employee_definition'
    _description = 'Choose manager for definition'

    name = fields.Char(string="Title")
    manager_id = fields.Many2one('hr.employee', string="Definition Manager")
    
    def print_report(self):
        employee_id = self.env.context.get('active_ids', [])
        datas = {
            'model': 'print.employee_definition',
            'form': self.read()[0],
            'employee_id': employee_id[0]
        }
        return self.env.ref('ubisol_hr_employee_upgrade.salary_specification_report_pdf').report_action(self, data=datas)
        