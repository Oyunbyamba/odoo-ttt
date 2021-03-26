# -*- coding: utf-8 -*-

from odoo import fields, models


class UbiLetterType(models.Model):
    _name = "ubi.letter.type"
    _description = " "
    name = fields.Char(string="Төрлийн нэр", groups="base.group_user")
    code = fields.Char(string="Код", groups="base.group_user")
