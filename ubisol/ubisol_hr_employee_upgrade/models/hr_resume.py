# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _, api

class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'
    diploma_number = fields.Char(string='Diploma number')
    education_degree_id = fields.Many2one('hr.education.degree', string="Education Degrees")
    company_name = fields.Char(string='Company name')
    is_highest_degree = fields.Boolean(string='Is highest degree')
    profession = fields.Char(string='Profession')
    position = fields.Char(string='Job position')

    @api.model
    def create(self, vals):
        resume = super(ResumeLine, self).create(vals)
        if resume.is_highest_degree:
            resume.employee_id.study_field = resume.profession
            resume.employee_id.study_school = resume.name
            resume.employee_id.certificate = resume.education_degree_id.name
        return resume

class EducationDegree(models.Model):
    """Table for keep education degree information"""

    _name = 'hr.education.degree'
    _description = 'HR Employee education degree'

    name = fields.Char(string='HR Education degree')

     