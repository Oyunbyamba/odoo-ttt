# -*- coding: utf-8 -*-

# from odoo import models, fields, api


from datetime import datetime, timedelta
from odoo import models, fields, _, api


class HrEmployeeFamilyInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.family'
    _description = 'HR Employee Family'

    employee_id = fields.Many2one('hr.employee', string="Employee", help='Select corresponding Employee',
                                  invisible=1)
    relation_id = fields.Many2one(
        'hr.employee.relation', string="Relation", help="Relationship with the employee")
    last_name = fields.Char(string='Lastname')
    member_name = fields.Char(string='Firstname')
    member_contact = fields.Char(string='Contact No')
    birth_date = fields.Date(string="DOB", tracking=True)
    birth_place = fields.Many2one('res.country.state', string="POB")
    current_job = fields.Char(string='Current job')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    surname = fields.Char(string='Surname')
    # family_name = fields.Char(string='Family Name')
    fam_ids = fields.One2many(
        'hr.employee.family', 'employee_id', string='Family', help='Family Information')

    @api.onchange('spouse_complete_name', 'spouse_birthdate')
    def onchange_spouse(self):
        relation = self.env.ref('hr_employee_updation.employee_relationship')
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


class EmployeeRelationInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.relation'

    name = fields.Char(string="Relationship",
                       help="Relationship with thw employee")
