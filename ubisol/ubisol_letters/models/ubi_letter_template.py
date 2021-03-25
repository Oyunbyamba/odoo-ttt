# -*- coding: utf-8 -*-

from odoo import fields, models


class UbiLetterTemplate(models.Model):
    _name = "ubi.letter.template"
    _description = " "
    name = fields.Char(string="name")
    types = fields.Selection([
    ('a4', 'a5'),
    ('a3', 'a2')], string="type")

    letter_description = fields.Html(string="Descrption")
