# -*- coding: utf-8 -*-

from odoo import fields, models


class UbiLetterSubject(models.Model):
    _name = "ubi.letter.subject"
    _description = " "
    name = fields.Char(string="name")
    code = fields.Char(string="code")
    desc = fields.Char(string="desc")
