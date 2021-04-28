# -*- coding: utf-8 -*-
import logging
from odoo import models, tools, fields, api, _
from datetime import date, datetime, timedelta, time
from bs4 import BeautifulSoup
import os
import json
import base64
import xml.etree.ElementTree as ET
import re
import ssl
import requests
from odoo.exceptions import ValidationError, AccessError, RedirectWarning

_logger = logging.getLogger(__name__)


class UbiLetter(models.AbstractModel):
    _name = "ubi.letter"
    _description = " Ubisol Letter"
    _rec_name = 'letter_number'


    card_number = fields.Integer(
        string='Картын дугаар', help="Картын дугаар", groups="base.group_user")
    letter_number = fields.Char(
        string='Баримтын дугаар', help="Баримтын дугаар", groups="base.group_user")
    register_number = fields.Integer(
        string='Бүртгэлийн дугаар', help="Бүртгэлийн дугаар", groups="base.group_user")
    letter_total_num = fields.Integer(
        string='Хуудасны тоо', help="Хуудасны тоо", groups="base.group_user")
    desc = fields.Char(string='Товч утга', groups="base.group_user")
    must_return_date = fields.Date(
        string='Хариу ирүүлэх огноо', default=datetime.now().strftime('%Y-%m-%d'), groups="base.group_user")
    received_date = fields.Date(
        string='Хүлээн авсан огноо', groups="base.group_user")
    registered_date = fields.Datetime(
        string='Бүртгэсэн огноо', default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), groups="base.group_user")
    letter_date = fields.Date(string='Баримтын огноо', default=datetime.today(),
                              groups="base.group_user")
    processing_datetime = fields.Datetime(string='Явцын огноо',
                                          default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), groups="base.group_user")
    # partner_ids = fields.Many2many(
    #     'res.partner', string='Хаанаас', groups="base.group_user")
    partner_id = fields.Many2one(
        'res.partner', string='Хаанаас', domain=[('ubi_letter_org', '=', True)], groups="base.group_user")
    department_id = fields.Many2one(
        'hr.department', string='Хариуцах Хэлтэс', related='responsible_employee_id.department_id', groups="base.group_user")

    to_user = fields.Char(compute='_compute_to_user', groups='base.group_user')    
    
    responsible_employee_id = fields.Many2one('hr.employee', string='Хэнд')
    request_employee_id = fields.Many2one('hr.employee', string='Хүсэлт илгээсэн ажилтан')

    official_person = fields.Char('Албан тушаалтан', groups="base.group_user")
    user_id = fields.Many2one('res.users', groups="base.group_user")
    confirm_user_id = fields.Many2one('res.users', groups="base.group_user")
    validate1_user_id = fields.Many2one('res.users', groups="base.group_user")
    validate_user_id = fields.Many2one('res.users', groups="base.group_user")

    letter_type_id = fields.Many2one(
        'ubi.letter.type', string='Баримтын төрөл', groups="base.group_user")
    letter_subject_id = fields.Many2one(
        'ubi.letter.subject', string='Баримтын тэргүү', groups="base.group_user")

    must_return = fields.Boolean(
        string='Хариутай эсэх', default=False, groups="base.group_user")
    is_reply_doc = fields.Boolean(
        string='Хариу бичсэн эсэх', default=False, groups="base.group_user")
    is_local = fields.Boolean(
        string='Дотоод бичиг', groups="base.group_user", default=True)
    is_head_company = fields.Boolean(
        string='Дээд газраас ирсэн', default=False, groups="base.group_user")
    tabs_id = fields.Integer('Tabs id', groups="base.group_user")
    computed_letter_type = fields.Char(
        string='Хариу бичгийн төрөл', compute='_computed_letter_type', groups="base.group_user")
    computed_letter_subject = fields.Char(
        string='Хариу бичгийн тэргүү', compute='_computed_letter_subject', groups="base.group_user")
    computed_letter_desc = fields.Char(
        string='Хариу бичгийн агуулга', compute='_computed_letter_desc', groups="base.group_user")
    src_document_number = fields.Char(
        string='Эх бичгийн дугаар', groups="base.group_user")
    src_document_code = fields.Char(
        string='Эх бичгийн цахим дугаар', groups="base.group_user")
    src_document_date = fields.Char(
        string='Эх бичгийн огноо', groups="base.group_user")
    priority_id = fields.Selection([('1', 'Энгийн'),
                                    ('2', 'Нууц'),
                                    ('3', 'Маш нууц'),
                                    ('4', 'Гарт нь'),
                                    ], default='1', string='Нууцлалын зэрэг', groups="base.group_user")

    def _compute_to_user(self):
        for letter in self:
            to_user = ''
            if letter.is_local:
                to_user = letter.responsible_employee_id.name
            else:
                to_user = letter.official_person
            letter.to_user = to_user
