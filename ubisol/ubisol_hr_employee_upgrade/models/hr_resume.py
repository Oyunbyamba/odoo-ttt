# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _, api

class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'
    diploma_number = fields.Char(string='Diploma number')
    education_degree_id = fields.Many2one('hr.education.degree', string="Education Degrees")
    company_name = fields.Char(string='Company name')
    is_highest_degree = fields.Boolean(string='Is highest degree')

    # @api.onchange('is_highest_degree')
    # def _onchange_is_highest_degree(self):
    #     if self.is_highest_degree:
    #         hr_employee = self.env['hr.employee'].search([('id','=',self.employee_id)])
    #         hr_employee.write('study_field', self.name)
        #    self.env['ir.config_parameter'].sudo().set_param("hr_resignation.no_of_days", self.no_of_days)

class EducationDegree(models.Model):
    """Table for keep education degree information"""

    _name = 'hr.education.degree'
    _description = 'HR Employee education degree'

    name = fields.Char(string='HR Education degree')    

     