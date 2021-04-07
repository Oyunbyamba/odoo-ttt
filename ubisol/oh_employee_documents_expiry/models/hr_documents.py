from odoo import models, fields


class HrDocument(models.Model):
    _name = 'hr.document'
    _description = 'Documents Template '

    name = fields.Char(string='Баримтын нэр', required=True, copy=False, help='You can give your'
                                                                               'Document name here.')
    note = fields.Html(string='Тодорхойлолт', copy=False, help="Note")
    attach_id = fields.Many2many('ir.attachment', 'attach_rel', 'doc_id', 'attach_id3', string="Хавсралт",
                                 help='You can attach the copy of your document', copy=False)