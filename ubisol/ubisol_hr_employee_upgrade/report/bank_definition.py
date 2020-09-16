from odoo import api, models, _
from odoo.exceptions import UserError

class ReportDefinitionPdf(models.AbstractModel):
    _name = 'report.ubisol_hr_employee_upgrade.report_definition_pdf'
    _description = 'Bank Definition Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # import pdb
        # pdb.set_trace()
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        
        docs = self.env['create.bank_definition'].browse(data['form']['id'])    
        employee = self.env['hr.employee'].browse(data['form']['employee_id'][0])
        return {
            'doc_model': 'hr.employee',
            'organization_name': str(data['form']['organization_name']).upper(),
            'employee': employee,
        }