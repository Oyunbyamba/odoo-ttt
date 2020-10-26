from odoo import api, models, _
from odoo.exceptions import UserError

class LeaveReportPdf(models.AbstractModel):
    _name = 'report.ubisol_hr_holidays.leave_report'
    _description = 'Employee Anket Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        ceo_employee_name = ''
        if(len(self.env['hr.employee'].search([('parent_id', '=', False)]).ids) == 1):
            ceo_employee_name = self.env['hr.employee'].search([('parent_id', '=', False)]).name
        leave_id = docids
        leave = self.env['hr.leave'].browse(leave_id)
        hours = self.env.company.resource_calendar_id.get_work_hours_count(leave.date_from, leave.date_to)
        return {
            'doc_model': 'hr.leave',
            'ceo_employee_name': ceo_employee_name,
            'leave': leave,
            'hours': hours
        }
