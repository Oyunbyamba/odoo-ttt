# -*- coding: utf-8 -*-

from odoo import fields, models


class UbiLetterTemplate(models.Model):
    _name = "ubi.letter.template"
    _description = "Баримтын загвар"
    _rec_name = 'letter_template_name'


    letter_template_name = fields.Char(string="Загварын нэр ", groups="base.group_user")
    letter_template = fields.Html(string="Загвар", groups="base.group_user")
    paper_size = fields.Selection(
        [('a4', 'A4'), ('a5', 'A5')],
        string="Цаасны хэмжээ", 
        groups="base.group_user")