# -*- coding: utf-8 -*-

from odoo import fields, models


class UbiLetterDocument(models.Model):
    _name = "ubi.letter.document"
    _description = " "

    document_id = fields.Integer(groups="base.group_user")
    
