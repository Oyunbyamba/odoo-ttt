# -*- coding: utf-8 -*-

from odoo import fields, models


class UbiLetterType(models.Model):
    _name = "ubi.letter.type"
    _description = " "
    name = fields.Char(string="Төрөлийн нэр")
    code = fields.Char(string="Код")
