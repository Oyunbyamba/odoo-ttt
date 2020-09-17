# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class ubisol_login_template(models.Model):
#     _name = 'ubisol_login_template.ubisol_login_template'
#     _description = 'ubisol_login_template.ubisol_login_template'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
