# -*- coding: utf-8 -*-

from odoo import fields, models


class UbiLetter(models.Model):
    _name = "ubi.letter"
    _description = " "

    is_local = fields.Boolean(string='Дотоод бичиг эсэх')
    is_received_letter = fields.Boolean(string='Ирсэн бичиг эсэх')
    card_number = fields.Char(string='Картын дугаар', help="Картын дугаар")
    letter_number = fields.Char(string='Бичгийн дугаар', help="Бичгийн дугаар")
    register_number = fields.Char(
        string='Бүртгэлийн дугаар', help="Бүртгэлийн дугаар")
    letter_total_num = fields.Integer(
        string='Хуудасны тоо', help="Хуудасны тоо")

    received_datetime = fields.Datetime(string='Хүлээн авсан огноо')
    registered_datetime = fields.Datetime(string='Бүртгэсэн огноо')
    return_datetime = fields.Datetime(string='Хариу өгөх огноо')
    must_return = fields.Boolean(string='Хариу өгөх эсэх', default='False')

    partner_id = fields.Many2one('res.partner', string='Холбогдогч тал')

    department_id = fields.Many2one('hr.department', string='Хариуцах Хэлтэс')
    employee_id = fields.Many2one('hr.employee', string='Хариуцах Хүн')

    state = fields.Selection(selection=[
        ('draft', 'Бүртгэсэн'),
        ('processing', 'Шийдвэрлэж байгаа'),
        ('cancelled', 'Цуцласан'),
        ('completed', 'Хаасан')],
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
