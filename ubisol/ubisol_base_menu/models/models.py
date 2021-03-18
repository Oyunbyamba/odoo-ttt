# -*- coding: utf-8 -*-

from odoo import models, fields, api


# class ubisol_base_menu(models.Model):
#     _name = 'ubisol_base_menu.ubisol_base_menu'
#     _description = 'ubisol_base_menu.ubisol_base_menu'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
