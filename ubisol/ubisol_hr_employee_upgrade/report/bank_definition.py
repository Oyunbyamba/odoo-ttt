from odoo import api, models, _


class ReportDefinitionPdf(models.AbstractModel):
    _name = 'report.ubisol_hr_employee_upgrade.report_definition'
    _description = 'Bank Definition Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if data['form']['employee_id']:
            bank_definition = self.env['ubisol_hr_employee_upgrade.bank_definition'].search([('employee_id', '=', data['form']['employee_id'][0])])
        else:
            bank_definition = self.env['ubisol_hr_employee_upgrade.bank_definition'].search([])
        return {
            'doc_model': 'hr.employee',
            'bank_definition': bank_definition,
        }
