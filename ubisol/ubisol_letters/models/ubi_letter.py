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

    is_local = fields.Boolean(string='Дотоод бичиг эсэх', groups="base.group_user")
    is_received_letter = fields.Boolean(string='Ирсэн бичиг эсэх', groups="base.group_user")
    card_number = fields.Char(string='Картын дугаар', help="Картын дугаар", groups="base.group_user")
    letter_number = fields.Char(
        string='Бичгийн дугаар', help="Бичгийн дугаар", groups="base.group_user")
    register_number = fields.Char(
        string='Бүртгэлийн дугаар', help="Бүртгэлийн дугаар", groups="base.group_user")
    letter_total_num = fields.Integer(
        string='Хуудасны тоо', help="Хуудасны тоо", groups="base.group_user")
    received_datetime = fields.Datetime(
        string='Хүлээн авсан огноо', groups="base.group_user")
    registered_datetime = fields.Datetime(
        string='Бүртгэсэн огноо', groups="base.group_user")
    return_datetime = fields.Datetime(
        string='Хариу өгөх огноо', groups="base.group_user")
    sent_datetime = fields.Datetime(
        string='Илгээх огноо', groups="base.group_user")

    partner_id = fields.Many2one(
        'res.partner', string='Холбогдогч тал', groups="base.group_user")
    letter_type_id = fields.Many2one(
        'ubi.letter.type', string='Албан бичгийн төрөл', groups="base.group_user")
    letter_subject_id = fields.Many2one(
        'ubi.letter.subject', string='Гарчиг ангилал', groups="base.group_user")
    letter_template_id = fields.Many2one(
        'ubi.letter.template', string='Албан бичгийн загвар', groups="base.group_user")
    letter_template_text = fields.Html(
        related="letter_template_id.letter_template", groups="base.group_user")
    custom_letter_template = fields.Html(
        'Custom text', groups="base.group_user")

    department_id = fields.Many2one(
        'hr.department', string='Хариуцах Хэлтэс', groups="base.group_user")
    employee_id = fields.Many2one(
        'hr.employee', string='Хариуцах Хүн', groups="base.group_user")
    where_sent = fields.Char(string='Хаашаа явах', groups="base.group_user")

    how_decide = fields.Char(string="Яаж шийдвэрлэх", groups="base.group_user")
    must_return = fields.Boolean(
        string='Хариу өгөх эсэх', default=False, groups="base.group_user")

    state = fields.Selection([
        ('draft', 'Хүлээн авах'),
        ('decide', 'Шийдвэрлэх'),
        ('reply', 'Хариу өгөх')],
        groups="base.group_user",
        default='draft',
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    state_going = fields.Selection([
        ('plan', 'Төлөвлөлт'),
        ('sent', 'Илгээх')], 
        groups="base.group_user",
        default='plan',
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)

    @api.onchange('letter_template_id')
    def _set_letter_template(self):
        if self.letter_template_text:
            self.custom_letter_template = self.letter_template_text

    
