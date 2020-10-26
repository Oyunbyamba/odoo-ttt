from odoo import fields, models, api

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    pin = fields.Char(related='employee_id.pin', string="PIN")
    fullname = fields.Char(compute="_compute_fullname", compute_sudo=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string="Хэлтэс", store=True)

    @api.depends("employee_id")
    def _compute_fullname(self):
        for record in self:
            employee = record.employee_id
            if employee.surname:
                fullname = employee.surname[0] + '.' + employee.name
            else:
                fullname = employee.name
            record.fullname = fullname