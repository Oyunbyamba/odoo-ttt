# -*- coding: utf-8 -*-

from odoo import fields, models


class LetterSubject(models.Model):
    _name = "letter.subject"
    _description = " "
    name = fields.Char(string="name")
    code = fields.Char(string="code")
    desc = fields.Char(string="desc")


class LetterType(models.Model):
    _name = "letter.type"
    _description = " "
    name = fields.Char(string="name")
    code = fields.Char(string="code")
