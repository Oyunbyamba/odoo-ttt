# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)

class HrEmployeeFamilyInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.family'
    _description = 'HR Employee Family'

    employee_id = fields.Many2one('hr.employee', string="Employee", help='Select corresponding Employee', invisible=1)
    relation_id = fields.Many2one('hr.employee.relation', string="Relation", help="Relationship with the employee")
    last_name = fields.Char(string='Lastname')
    member_name = fields.Char(string='Firstname')
    member_contact = fields.Char(string='Contact No')
    birth_date = fields.Date(string="DOB", tracking=True)
    birth_place = fields.Many2one('res.country.state', string="Birth place")
    current_job = fields.Char(string='Current job')
    address_id = fields.Many2one('res.partner', string='Address')

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    surname = fields.Char(string='Surname')
    family_name = fields.Char(string='Family Name', groups="hr.group_hr_user")
    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family', help='Family Information', groups="hr.group_hr_user")
    home_owner = fields.Selection([
        ('own', 'Өөрийн'),
        ('parent', 'Эцэг, эх'),
        ('tenancy', 'Түрээсийн'),
        ('laon', 'Зээл')
    ], string='Home owner', default='own', tracking=True, groups="hr.group_hr_user")
    ethnicity = fields.Many2one('hr.employee.ethnicity', string="Ethnicity", help="Ethnicity with the employee", groups="hr.group_hr_user")
    social_status = fields.Char('Нийгмийн гарал', groups="hr.group_hr_user")
    family_income = fields.Float('Family Income', digits=(12,0), groups="hr.group_hr_user")
    is_served_in_military = fields.Selection([
        ('yes', 'Тийм'),
        ('no', 'Үгүй')
    ], string='Is served in the military', default='yes', groups="hr.group_hr_user")
    driving_classification = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E')
    ], string='Driving Classification', groups="hr.group_hr_user")
    driver_license_number = fields.Char(string="Driver's license number", groups="hr.group_hr_user")
    driver_blood_type = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')
    ], string="Driver's blood type", groups="hr.group_hr_user")
    certificate = fields.Selection(selection=[
        ('Ерөнхий боловсрол', 'Ерөнхий боловсрол'),
        ('Тусгай дунд боловсрол', 'Тусгай дунд боловсрол'),
        ('Дээд боловсрол', 'Дээд боловсрол'),
        ('Магистр', 'Магистр'),
        ('Доктор', 'Доктор'),
        ('Бусад', 'Бусад'),
    ])
    years_of_driving = fields.Integer(string='Years of driving', groups="hr.group_hr_user")
    relative_employee_id = fields.Many2one('hr.employee', 'Relative', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", groups="hr.group_hr_user")
    size_of_shirt = fields.Char(string='The size of shirt', groups="hr.group_hr_user")
    size_of_pants = fields.Char(string='The size of pants', groups="hr.group_hr_user")
    size_of_shoes = fields.Char(string='The size of shoes', groups="hr.group_hr_user")
    create_contract = fields.Boolean(string='Create contract', groups="hr.group_hr_user")
    contract_ids = fields.One2many('hr.contract', 'employee_id', string='Contract', groups="hr.group_hr_user")
    contract_signed_date = fields.Date(string="Contract signed date", groups="hr.group_hr_user")
    years_of_civil_service = fields.Integer(string='Years', groups="hr.group_hr_user")
    latitude = fields.Char('Өргөрөг', groups="hr.group_hr_user")
    longitude = fields.Char('Уртраг', groups="hr.group_hr_user")
    employee_pictures = fields.One2many('hr.employee.picture', 'employee_id', string='Employee picture', groups="hr.group_hr_user")
    # image=fields.Binary(compute='_getBase64Image') 
    departure_reason = fields.Selection(selection_add=[('other', 'Бусад')], groups="hr.group_hr_user")
    resign_date = fields.Date('Resign Date', compute='_compute_resign_date', inverse='_set_document', store=True, groups="hr.group_hr_user")
    is_disabled = fields.Boolean('Хөгжлийн бэрхшээлтэй эсэх', default=False, groups="hr.group_hr_user")
    is_in_group = fields.Boolean('Группд байдаг эсэх', default=False, groups="hr.group_hr_user")
    employee_code = fields.Char('Ажилтаны код', groups="hr.group_hr_user")
    rfid_code = fields.Char('Картын дугаар', groups="hr.group_hr_user")
    attendance_ids = fields.One2many('hr.attendance', 'employee_id', string='Employee attendance', groups="hr.group_hr_user")
    emergency_person = fields.Char(string='Таны юу болох', groups="hr.group_hr_user")

    @api.constrains('pin', 'identification_id')
    def _check_pin(self):
        if self.pin:
            same_pin = self.env['hr.employee'].search_count([('pin', '=', self.pin), ('id', '!=', self.id)])
            if same_pin > 0:
                raise ValidationError("Давхардсан пин кодтой ажилтан байна.")

        if self.identification_id:        
            same_regno = self.env['hr.employee'].search_count([('identification_id', 'ilike', self.identification_id), ('id', '!=', self.id)])
            if(same_regno) > 0:
                raise ValidationError("Давхардсан регистрийн дугаартай ажилтан байна.")

    @api.onchange('spouse_complete_name', 'spouse_birthdate')
    def onchange_spouse(self):
        relation = self.env.ref('ubisol_hr_employee_upgrade.employee_relationship_spouse')
        lines_info = []
        spouse_name = self.spouse_complete_name
        date = self.spouse_birthdate
        if spouse_name and date:
            lines_info.append((0, 0, {
                'member_name': spouse_name,
                'relation_id': relation.id,
                'birth_date': date,
            }))
        self.fam_ids = [(6, 0, 0)] + lines_info  

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        if(self.parent_id.user_id):
            self.leave_manager_id = self.parent_id.user_id
        else:
           self.leave_manager_id = 0

    @api.onchange('identification_id')
    def onchange_identification_id(self):
        if self.identification_id:    
            self.identification_id = str(self.identification_id).upper()   
        else:
            self.identification_id = ''

    @api.depends('departure_reason')
    def _compute_resign_date(self):
        for employee in self:
            if(employee.departure_reason):
                employee.resign_date = fields.Date.context_today(self)
            else:
                employee.resign_date = fields.Date.context_today(self)
    
    def _set_document(self):
        for employee in self:
            employee.resign_date = employee.resign_date

    def _prepare_contract_values(self, employee):
        trial_date = employee.contract_signed_date + relativedelta(months=3)
        values = {
            'name': employee.name,
            'employee_id': employee.id,
            'date_start': employee.contract_signed_date,
            'department_id': employee.department_id.id,
            'job_id': employee.job_id.id,
            'wage': 0,
            'trial_date_end': trial_date
        }
        if employee.contract_id:
            employee_contract = self.env['hr.contract'].browse(self.contract_id.id)
            employee_contract.write(values)
        else:    
        #     if(trial_date < fields.Date.context_today(self)):
        #         values['state'] = 'open'
        #         values['kanban_state'] = 'done'
        #     else:
        #         values['state'] = 'draft'
        #         values['kanban_state'] = 'donnormale'
            employee_contract = self.env['hr.contract'].create(values)    

        return employee_contract        

    @api.model
    def create(self, vals):
        employee = super(HrEmployee, self).create(vals)
        if employee.contract_signed_date:
            employee_contract = self._prepare_contract_values(employee)

        #create schedule & workplan for employee when employee has department
        if employee.department_id:
            shift = self.env['hr.employee.shift'].search([
                ('hr_department', '=', vals.get('department_id')),
                ('assign_type', '=', 'department')], limit=1, order='id desc')

            if shift:
                log_obj = self.env["hr.employee.shift"].search([])
                employee_id = [[6, False, [employee.id]]]
                values = {
                    'name': shift.name,
                    'assign_type': 'employee',
                    'hr_department': [],
                    'hr_employee': employee_id,
                    'resource_calendar_ids': shift.resource_calendar_ids.id,
                    'date_from': str(shift.date_from),
                    'date_to': str(shift.date_to)
                }         
                log_obj._create_schedules(values, shift)

        return employee

    def write(self, vals):
        prev_department_id = self._origin.department_id
        employee = super(HrEmployee, self).write(vals)  
        if vals.get('contract_signed_date') and vals.get('create_contract'):    
            employee_contract = self._prepare_contract_values(self)        

        #if this employee has child employees, then their leave_manager_id is set by self.user_id
        if self.user_id:
            child_employees = self.env['hr.employee'].search([('parent_id', '=', self._origin.id)])
            for child_employee in child_employees:
                child_employee.parent_id = self.id

        #create schedule for employee when employee's department selected
        if vals.get('department_id') and (vals.get('department_id') != prev_department_id):
            shifts = self.env['hr.employee.shift'].search([
                ('hr_department', '=', vals.get('department_id')),
                ('assign_type', '=', 'department')])

            if len(shifts) > 0:
                log_obj = self.env["hr.employee.shift"].search([])
                employee_id = [[6, False, [self.id]]]
                for shift in shifts:
                    values = {
                        'name': shift.name,
                        'assign_type': 'employee',
                        'hr_department': [],
                        'hr_employee': employee_id,
                        'resource_calendar_ids': shift.resource_calendar_ids.id,
                        'date_from': str(shift.date_from),
                        'date_to': str(shift.date_to)
                    }
                    date_from = datetime.strftime(shift.date_from, '%Y-%m-%d')
                    date_to = datetime.strftime(shift.date_to, '%Y-%m-%d')
                    prev_schedule = self.env['hr.employee.schedule'].search(
                        [('hr_employee', '=', self.id), ('work_day', '>=', date_from), ('work_day', '<=', date_to)]).unlink()         
                    # log_obj._check_duplicated_schedules(values)
                    log_obj._create_schedules(values, shift)        

        return employee    

    def toggle_active(self):
        res = super(HrEmployee, self).toggle_active()
        self.filtered(lambda employee: employee.active).write({
            'departure_reason': False,
            'departure_description': False,
        })
        
        if len(self.ids) >= 1 and not self[0].active:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Register Departure'),
                'res_model': 'hr.departure.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'active_ids': self.ids},
                'views': [[False, 'form']]
            }
        return res

    @api.model
    def get_my_attendances(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        return employee.attendance_ids
            

class EmployeeRelationInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.relation'
    _description = 'HR Employee Relation'

    name = fields.Char(string="Relationship", help="Relationship with the employee")

class EmployeeEthnicity(models.Model):
    """Table for keep ethnicity information"""

    _name = 'hr.employee.ethnicity'
    _description = 'HR Employee Ethnicity'

    name = fields.Char(string="Ethnicity", help="Ethnicity with the employee")
                  
class EmployeePicture(models.Model):
    """Table for keep ethnicity information"""

    _name = 'hr.employee.picture'
    _description = 'HR Employee Picture'

    name = fields.Char(string="Check in img")
    employee_id = fields.Many2one('hr.employee', string="Employee", ondelete='cascade')   
    check_in = fields.Datetime(string="Check In")
    check_out = fields.Datetime(string="Check Out")   
    second_pic = fields.Char(string="Check out img")

class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'
    surname = fields.Char(string='Surname')

class Contract(models.Model):
    _inherit = 'hr.contract'