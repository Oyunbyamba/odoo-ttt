# -*- coding: utf-8 -*-

from odoo import fields, models


class LetterType(models.Model):
    _name = "letter.type"
    _description = " "
    name = fields.Char(string="name")
    code = fields.Char(string="code")
