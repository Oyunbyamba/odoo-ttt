from odoo import api, models, _
from odoo.exceptions import UserError

class LeaveReportPdf(models.AbstractModel):
    _name = 'report.ubisol_hr_holidays.leave_report'
    _description = 'Employee Anket Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('______ceo_________')
        ceo_employee_name = self.env['hr.employee'].search([('parent_id', '=', 3)]).name
        print(ceo_employee_name)
        leave_id = self.env.context.get('active_ids', [])
        print(leave_id)
        leave = self.env['hr.leave'].browse(leave_id)
        return {
            'doc_model': 'hr.leave',
            'ceo_employee_name': ceo_employee_name,
            'leave': leave,
        }
