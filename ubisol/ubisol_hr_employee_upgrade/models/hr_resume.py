# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _, api

class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'
    diploma_number = fields.Char(string='Diploma number')
    education_degree_id = fields.Many2one('hr.education.degree', string="Education Degrees")


class EducationDegree(models.Model):
    """Table for keep education degree information"""

    _name = 'hr.education.degree'
    _description = 'HR Employee education degree'

    name = fields.Char(string='HR Education degree')    