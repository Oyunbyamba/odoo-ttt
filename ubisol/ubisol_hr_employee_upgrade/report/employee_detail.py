from odoo import api, models, _
from odoo.exceptions import UserError

class EmployeeDetailPdf(models.AbstractModel):
    _name = 'report.ubisol_hr_employee_upgrade.employee_detail_report'
    _description = 'Employee Anket Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        employee = self.env['hr.employee'].browse(docids)
        resume_lines = self.env['hr.resume.line'].search([('employee_id', 'in', docids)])
        employee_skills = self.env['hr.employee.skill'].search([('employee_id', 'in', docids)])

        return {
            'doc_model': 'hr.employee',
            'docs': employee,
            'resume_lines': resume_lines,
            'employee_skills': employee_skills
        }