# -*- coding: utf-8 -*-

from odoo import fields, models


class UbiLetterSubject(models.Model):
    _name = "ubi.letter.subject"
    _description = " "
    name = fields.Char(string="Гарчиг нэр", groups="base.group_user")
    code = fields.Char(string="код", groups="base.group_user")
    desc = fields.Char(string="Тайлбар", groups="base.group_user")
