from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class ReportDefinitionPdf(models.AbstractModel):
    _name = 'report.ubisol_hr_employee_upgrade.employee_working_report'
    _description = 'Quarantine Working Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # import pdb
        # pdb.set_trace()
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        
        employee = self.env['hr.employee'].browse(data['employee'])
        date = datetime.now().strftime('%Y.%m.%d')
        return {
            'doc_model': 'hr.employee',
            'document_order': str(data['form']['document_order']),
            'docs': employee,
            'date': date
        }