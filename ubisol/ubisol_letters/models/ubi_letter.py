# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from datetime import date, datetime, timedelta, time


_logger = logging.getLogger(__name__)

class UbiLetter(models.Model):
    _name = "ubi.letter"
    _description = " "

 
    def _get_default_note(self):
        result = """
            <div>
                <p class="terms">Payment terms are</p>
                <ul><li>15% in advance</li><ul/>
            </div>"""
        
        return result
    follow_id = fields.Many2one('ubi.letter', groups="hr.group_hr_user")
    draft_user_id = fields.Many2one('res.users', groups="hr.group_hr_user")
    monitor_user_id = fields.Many2one('res.users', groups="hr.group_hr_user")
    signed_user_id = fields.Many2one('res.users', groups="hr.group_hr_user")
    document_ids = fields.Many2many('ir.attachment',  string="Хавсралт", copy=False)
 
    is_local = fields.Boolean(string='Дотоод бичиг', groups="hr.group_hr_user")
    letter_status = fields.Selection([
        ('coming', 'Ирсэн'),
        ('going', 'Явсан'),
        ('planning', 'Төлөвлөлт')],
        groups="hr.group_hr_user",
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    card_number = fields.Integer(string='Картын дугаар', help="Картын дугаар", groups="hr.group_hr_user")
    letter_number = fields.Integer(string='Бичгийн дугаар', help="Бичгийн дугаар", groups="hr.group_hr_user")
    register_number = fields.Integer(string='Бүртгэлийн дугаар', help="Бүртгэлийн дугаар", groups="hr.group_hr_user")
    letter_total_num = fields.Integer(string='Хуудасны тоо', help="Хуудасны тоо", groups="hr.group_hr_user")
    desc = fields.Char(string='Товч утга', groups="hr.group_hr_user")
    received_date= fields.Date(string='Хүлээн авсан огноо', groups="hr.group_hr_user")
    registered_date = fields.Date(string='Бүртгэсэн огноо', groups="hr.group_hr_user")
    return_date = fields.Date(string='Шийдвэрлэх огноо', groups="hr.group_hr_user")
    letter_date = fields.Date(string='Бичгийн огноо', groups="hr.group_hr_user")

    partner_id = fields.Many2many('res.partner', string='Хаанаас', groups="hr.group_hr_user")
    letter_type_id = fields.Many2one('ubi.letter.type', string='Бичгийн төрөл', groups="hr.group_hr_user")
    letter_subject_id = fields.Many2one('ubi.letter.subject', string='Бичгийн тэргүү', groups="hr.group_hr_user")
    letter_template_id = fields.Many2one('ubi.letter.template', string='Бичгийн загвар', groups="hr.group_hr_user")
    letter_template_text = fields.Html(related="letter_template_id.letter_template", groups="hr.group_hr_user")
    custom_letter_template = fields.Html('Custom text', groups="hr.group_hr_user", default=_get_default_note)
    department_id = fields.Many2one('hr.department', string='Хариуцах Хэлтэс', groups="hr.group_hr_user")
    user_id = fields.Many2one('res.users', string='Хэнд', groups="hr.group_hr_user")
    
    must_return = fields.Boolean(string='Хариу өгөх', default=False, groups="hr.group_hr_user")
    is_head_company = fields.Boolean(string='Дээд газраас ирсэн', default=False, groups="hr.group_hr_user")
    state = fields.Selection([
        ('draft', 'Боловсруулах'),
        ('validate', 'Хянах'),
        ('validate1', 'Зөвшөөрсөн'),
        ('confirm', 'Баталсан')],
        groups="hr.group_hr_user",
        default='draft',
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    receiving_state = fields.Selection([
        ('receiving', 'receiving')],
        groups="hr.group_hr_user",
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    return_state = fields.Selection([
        ('return', 'return')],
        groups="hr.group_hr_user",
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)

    @api.onchange('letter_template_id')
    def _set_letter_template(self):
        if self.letter_template_text:
            self.custom_letter_template = self.letter_template_text

    
 
    
