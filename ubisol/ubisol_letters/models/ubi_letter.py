# -*- coding: utf-8 -*-

from odoo import fields, models




class UbiLetter(models.Model):
    _name = "ubi.letter"
    _description = " "

    def ubi_letter_processing_next(self):
        for rec in self:
            rec.state = 'processing'

    def ubi_letter_cancelled_next(self):
        for rec in self:
            rec.state = 'cancelled'

    def ubi_letter_completed_next(self):
        for rec in self:
            rec.state = 'completed'

  

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
    letter_type_id = fields.Many2one('ubi.letter.type', string='Албан бичгийн төрөл')
    letter_subject_id = fields.Many2one('ubi.letter.subject', string='Гарчиг ангилал')


    department_id = fields.Many2one('hr.department', string='Хариуцах Хэлтэс')
    employee_id = fields.Many2one('hr.employee', string='Хариуцах Хүн')
    where_sent = fields.Char(string='Хаашаа явах')

    state = fields.Selection([
        ('draft', 'Бүртгэсэн'),
        ('processing', 'Шийдвэрлэж байгаа'),
        ('cancelled', 'Цуцласан'),
        ('completed', 'Хаасан')], 
        default='draft',
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    
