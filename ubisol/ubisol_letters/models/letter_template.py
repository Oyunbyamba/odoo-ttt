# -*- coding: utf-8 -*-

from odoo import fields, models


class LetterTemplate(models.Model):
    _name = "letter.template"
    _description = " "
    name = fields.Char(string="name")
    types = fields.Selection([
    ('a4', 'a5'),
    ('a3', 'a2')], string="type")

    letter_description = fields.Html(string="Descrption")
