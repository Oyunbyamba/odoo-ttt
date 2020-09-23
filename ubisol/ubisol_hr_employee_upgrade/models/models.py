# -*- coding: utf-8 -*-

# from odoo import models, fields, api


from datetime import datetime, timedelta
from odoo import models, fields, _, api


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
    family_name = fields.Char(string='Family Name')
    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family', help='Family Information')
    home_owner = fields.Selection([
        ('own', 'Өөрийн'),
        ('parent', 'Эцэг, эх'),
        ('tenancy', 'Түрээсийн'),
        ('laon', 'Зээл')
    ], string='Home owner', default='own', tracking=True)
    ethnicity = fields.Many2one('hr.employee.ethnicity', string="Ethnicity", help="Ethnicity with the employee")
    family_income = fields.Float('Family Income', digits=(12,0))
    is_served_in_military = fields.Selection([
        ('yes', 'Тийм'),
        ('no', 'Үгүй')
    ], string='Is served in the military', default='yes')
    driving_classification = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E')
    ], string='Driving Classification')
    driver_license_number = fields.Char(string="Driver's license number")
    driver_blood_type = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')
    ], string="Driver's blood type")
    years_of_driving = fields.Integer(string='Years of driving')
    relative_employee_id = fields.Many2one('hr.employee', 'Relative', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    size_of_shirt = fields.Char(string='The size of shirt')
    size_of_pants = fields.Char(string='The size of pants')
    size_of_shoes = fields.Char(string='The size of shoes')
    create_contract = fields.Boolean(string='Create contract')
    contract_ids = fields.One2many('hr.contract', 'employee_id', string='Contract')
    contract_signed_date = fields.Date(string="Contract signed date")
    years_of_civil_service = fields.Integer(string='Years')

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
        print('____parent id______')
        print(self.parent_id.user_id)
        if(self.parent_id.user_id):
            self.leave_manager_id = self.parent_id.user_id
        else:
           self.leave_manager_id = 0   
        
    @api.model
    def create(self, vals):
        employee = super(HrEmployee, self).create(vals)
        contract_values = []
        if employee.contract_signed_date:
                contract_values.append({
                    'name': self.name,
                    'employee_id': self.id,
                    'date_start': self.contract_signed_date,
                    'department_id': self.department_id.id,
                    'job_id': self.job_id.id,
                    'wage': 0
                })
                hr_contract = self.env['hr.contract'].create(contract_values)
                hr_contract.write({'state': 'open', 'kanban_state': 'done'})
        return employee

    def write(self, vals):
        employee = super(HrEmployee, self).write(vals)
        contract_values = []
        if(self.contract_id.id == 0): 
            if self.contract_signed_date and self.create_contract:           
                contract_values.append({
                    'name': self.name,
                    'employee_id': self.id,
                    'date_start': self.contract_signed_date,
                    'department_id': self.department_id.id,
                    'job_id': self.job_id.id,
                    'wage': 0
                })
                hr_contract = self.env['hr.contract'].create(contract_values)
                hr_contract.write({'state': 'open', 'kanban_state': 'done'})
                self.contract_id = hr_contract.id
        else:
            if self.contract_signed_date:           
                prev_hr_contract = self.env['hr.contract'].browse(self.contract_id.id)
                prev_hr_contract.name = self.name
                prev_hr_contract.date_start = self.contract_signed_date
                prev_hr_contract.department_id = self.department_id.id
                prev_hr_contract.job_id = self.job_id.id
        return employee    

class EmployeeRelationInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.relation'
    _description = 'HR Employee Relation'

    name = fields.Char(string="Relationship",
                       help="Relationship with the employee")

class EmployeeEthnicity(models.Model):
    """Table for keep ethnicity information"""

    _name = 'hr.employee.ethnicity'
    _description = 'HR Employee Ethnicity'

    name = fields.Char(string="Ethnicity",
                       help="Ethnicity with the employee")
                  