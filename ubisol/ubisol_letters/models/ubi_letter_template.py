# -*- coding: utf-8 -*-

from odoo import fields, models


class UbiLetterTemplate(models.Model):
    _name = "ubi.letter.template"
    _description = " "
    letter_template_name = fields.Char(string="Загварын нэр ", groups="base.group_user")
    letter_template = fields.Html(string="Загвар", groups="base.group_user")
