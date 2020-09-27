from odoo import api, models, _
from odoo.exceptions import UserError

class LeaveReportPdf(models.AbstractModel):
    _name = 'report.ubisol_hr_holidays.leave_report_pdf'
    _description = 'Employee Anket Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # import pdb
        # pdb.set_trace()
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        
        # docs = self.env['create.bank_definition'].browse(data['form']['id'])    
        employee = self.env['hr.employee'].browse(data['employee'])
        return {
            'doc_model': 'hr.employee',
            'employee': employee,
        }