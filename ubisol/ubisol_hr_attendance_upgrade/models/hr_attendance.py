from odoo import fields, models, api

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _default_employee(self):
        return self.env.user.employee_id

    def _employee_id_domain(self):
        if self.user_has_groups('hr_attendance.group_hr_attendance_user') or self.user_has_groups('hr_attendance.group_hr_attendance_manager'):
            return []
        if self.user_has_groups('ubisol_hr_attendance_upgrade.group_hr_attendance_responsible'):
            return ['|', ('parent_id', '=', self.env.user.employee_id.id), ('user_id', '=', self.env.user.id)]
        return [('user_id', '=', self.env.user.id)]

    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  default=_default_employee, domain=_employee_id_domain,
                                  required=True, ondelete='cascade', index=True)
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