# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from datetime import date, datetime, timedelta, time


_logger = logging.getLogger(__name__)

class UbiLetter(models.Model):
    _name = "ubi.letter"
    _description = " "
    
    def ubi_letter_decide_next(self):
        for rec in self:
            rec.state = 'decide'

    def ubi_letter_reply_next(self):
        for rec in self:
            rec.state = 'reply'

    def ubi_letter_sent_next(self):
        for rec in self:
            rec.state_going = 'sent'

    def ubi_letter_prev(self):
        for rec in self:
            rec.state_going = 'plan'

    is_local = fields.Boolean(string='Дотоод бичиг эсэх', groups="hr.group_hr_user")
    is_received_letter = fields.Boolean(string='Ирсэн бичиг эсэх', groups="hr.group_hr_user")
    card_number = fields.Char(string='Картын дугаар', help="Картын дугаар", groups="hr.group_hr_user")
    letter_number = fields.Char(
        string='Бичгийн дугаар', help="Бичгийн дугаар", groups="hr.group_hr_user")
    register_number = fields.Char(
        string='Бүртгэлийн дугаар', help="Бүртгэлийн дугаар", groups="hr.group_hr_user")
    letter_total_num = fields.Integer(
        string='Хуудасны тоо', help="Хуудасны тоо", groups="hr.group_hr_user")
    received_datetime = fields.Datetime(
        string='Хүлээн авсан огноо', groups="hr.group_hr_user")
    registered_datetime = fields.Datetime(
        string='Бүртгэсэн огноо', groups="hr.group_hr_user")
    return_datetime = fields.Datetime(
        string='Хариу өгөх огноо', groups="hr.group_hr_user")
    sent_datetime = fields.Datetime(
        string='Илгээх огноо', groups="hr.group_hr_user")

    partner_id = fields.Many2one(
        'res.partner', string='Хэнээс', groups="hr.group_hr_user")
    letter_type_id = fields.Many2one(
        'ubi.letter.type', string='Бичгийн төрөл', groups="hr.group_hr_user")
    letter_subject_id = fields.Many2one(
        'ubi.letter.subject', string='Гарчиг ангилал', groups="hr.group_hr_user")

    letter_template_id = fields.Many2one(
        'ubi.letter.template', string='Бичгийн загвар', groups="hr.group_hr_user")

    letter_template_text = fields.Html(
        related="letter_template_id.letter_template", groups="hr.group_hr_user")
    custom_letter_template = fields.Html(
        'Custom text', groups="hr.group_hr_user")

    department_id = fields.Many2one(
        'hr.department', string='Хариуцах Хэлтэс', groups="hr.group_hr_user")
    employee_id = fields.Many2one(
        'hr.employee', string='Хэнд', groups="hr.group_hr_user")
    where_sent = fields.Char(string='Хаашаа явах', groups="hr.group_hr_user")

    how_decide = fields.Char(string="Яаж шийдвэрлэх", groups="hr.group_hr_user")
    must_return = fields.Boolean(
        string='Хариу өгөх эсэх', default=False, groups="hr.group_hr_user")

    state = fields.Selection([
        ('draft', 'Хүлээн авах'),
        ('decide', 'Шийдвэрлэх'),
        ('reply', 'Хариу өгөх')],
        groups="hr.group_hr_user",
        default='draft',
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    state_going = fields.Selection([
        ('plan', 'Төлөвлөлт'),
        ('sent', 'Илгээх')], 
        groups="hr.group_hr_user",
        default='plan',
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)

    @api.onchange('letter_template_id')
    def _set_letter_template(self):
        if self.letter_template_text:
            self.custom_letter_template = self.letter_template_text


 
    
