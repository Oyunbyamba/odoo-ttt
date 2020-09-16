from odoo import api, models, _

class ReportDefinitionPdf(models.AbstractModel):
    _name = 'report.ubisol_hr_employee_upgrade.report_definition'
    _description = 'Bank Definition Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # import pdb
        # pdb.set_trace()
        docs = self.env['create.bank_definition'].browse(data['form']['id'])    
        employee = self.env['hr.employee'].browse(data['form']['employee_id'][0])
        return {
            'doc_model': 'hr.employee',
            'docs': docs,
            'employee': employee
        }