from odoo import api, models, _
from odoo.exceptions import UserError

class ReportDefinitionPdf(models.AbstractModel):
    _name = 'report.ubisol_hr_employee_upgrade.report_specification'
    _description = 'Employee Definition Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # import pdb
        # pdb.set_trace()
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        
        employee = self.env['hr.employee'].browse(data['employee_id'])
    
        return {
            'doc_model': 'hr.employee',
            'docs': employee,
            'manager': data['form']['manager_id'][1],
            'title': str(data['form']['name']).upper(),
        }