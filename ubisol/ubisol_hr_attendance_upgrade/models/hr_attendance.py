from odoo import fields, models, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import logging

_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    _order = "id, check_in, check_out"

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
    pin = fields.Char(compute="_compute_pin", compute_sudo=True, search='_pin_search')
    fullname = fields.Char(compute="_compute_fullname", compute_sudo=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string="Хэлтэс", store=True)

    start_date = fields.Date(compute="_compute_start_date", inverse="_set_start_date", compute_sudo=True)
    end_date = fields.Date(compute="_compute_end_date", inverse="_set_start_date", compute_sudo=True)
    calculate_type = fields.Selection([
        ('department', 'Хэлтэс'),
        ('employee', 'Ажилтан')
    ], compute="_compute_calculate_type", inverse="set_calculate_type")

    @api.depends("employee_id")
    def _compute_start_date(self):
        for record in self:
            sdate = datetime.today() - relativedelta(months=+1)
            record.start_date = sdate.strftime('%Y-%m-20')
            
    def _set_start_date(self):
        for record in self:
            record.start_date = record.start

    @api.depends("employee_id")
    def _compute_end_date(self):
        for record in self:
            now = datetime.now()
            record.end_date = now.strftime('%Y-%m-%d')

    def _set_end_date(self):
        for record in self:
            record.end_date = record.end_date 

    @api.depends("employee_id")
    def _compute_fullname(self):
        for record in self:
            employee = record.employee_id
            if employee.surname:
                fullname = employee.surname[0] + '.' + employee.name
            else:
                fullname = employee.name
            record.fullname = fullname

    @api.depends("employee_id")
    def _compute_pin(self):
        for record in self:
            pin = ''
            if record.employee_id.pin:
                pin = record.employee_id.pin
            
            record.pin = pin

    @api.model
    def get_my_attendances(self):
        resource = self.env['resource.resource'].search([('user_id','=',self.env.user.id)])
        employee = self.env['hr.employee'].search([('resource_id','=',resource.id)])

        attendances = self.env['hr.attendance.report'].search([('hr_employee', '=', employee.id)])
        raw_data = attendances.read()
        return raw_data

    def _pin_search(self, operator, value):
        employee_ids = self.env['hr.employee'].search([('pin', '=', value)]).ids
        
        return [('employee_id', 'in', employee_ids)]
       