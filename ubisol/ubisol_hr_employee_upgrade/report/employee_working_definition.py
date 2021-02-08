from odoo import api, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class EmployeeDetailPdf(models.AbstractModel):
    _name = 'report.ubisol_hr_employee_upgrade.employee_working_report'
    _description = 'Employee Working Definition'

    @api.model
    def _get_report_values(self, docids, data=None):
        employees = self.env['hr.employee'].search([], limit=500, order='id asc')
        _logger.info(employees.search([], limit=500, order='id desc'))

        return {
            'doc_model': 'hr.employee',
            'docs': employees
        }