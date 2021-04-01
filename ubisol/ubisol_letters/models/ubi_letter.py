# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from datetime import date, datetime, timedelta, time
from requests import Session
from zeep import Client
from zeep.transports import Transport

import xml.etree.ElementTree as ET

import ssl
import requests

_logger = logging.getLogger(__name__)


class UbiLetter(models.Model):
    _name = "ubi.letter"
    _description = " "
    _rec_name = 'letter_number'

    def _get_default_note(self):
        result = """"""
        return result

    follow_id = fields.Many2one('ubi.letter', groups="base.group_user")
    draft_user_id = fields.Many2one('res.users', groups="base.group_user")
    confirm_user_id = fields.Many2one('res.users', groups="base.group_user")
    validate_user_id = fields.Many2one('res.users', groups="base.group_user")

    letter_attachment_id = fields.Many2many('ir.attachment', 'letter_doc_attach', 'letter_id', 'doc_id', string="Хавсралт", copy=False)

    is_local = fields.Boolean(string='Дотоод бичиг', groups="base.group_user", default=False)
    letter_status = fields.Selection([
        ('coming', 'Ирсэн'),
        ('going', 'Явсан'),
        ('planning', 'Төлөвлөлт')],
        groups="base.group_user",
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
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
        string='Хүлээн авсан огноо', default=datetime.now().strftime('%Y-%m-%d'), groups="base.group_user")
    registered_date = fields.Datetime(
        string='Бүртгэсэн огноо', default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), groups="base.group_user")
    decide_date = fields.Date(
        string='Шийдвэрлэх огноо', default=datetime.now().strftime('%Y-%m-%d'), groups="base.group_user")
    letter_date = fields.Date(string='Баримтын огноо', groups="base.group_user")
    processing_datetime = fields.Datetime(string='Явцын огноо', default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), groups="base.group_user")
    # partner_ids = fields.Many2many(
    #     'res.partner', string='Хаанаас', groups="base.group_user")
    partner_id = fields.Many2one(
        'res.partner', string='Хаанаас', groups="base.group_user")
    letter_type_id = fields.Many2one(
        'ubi.letter.type', string='Баримтын төрөл', groups="base.group_user")
    letter_subject_id = fields.Many2one(
        'ubi.letter.subject', string='Баримтын тэргүү', groups="base.group_user")
    letter_template_id = fields.Many2one(
        'ubi.letter.template', string='Баримтын загвар', groups="base.group_user")
    letter_template_text = fields.Html(
        related="letter_template_id.letter_template", groups="base.group_user")
    custom_letter_template = fields.Html(
        'Custom text', groups="base.group_user", default=_get_default_note)
    department_id = fields.Many2one(
        'hr.department', string='Хариуцах Хэлтэс', groups="base.group_user")
    user_id = fields.Many2one(
        'res.users', string='Хэнд')
    official_person = fields.Char('Албан тушаалтан', groups="base.group_user")
    must_return = fields.Boolean(
        string='Хариу өгөх', default=False, groups="base.group_user")
    is_head_company = fields.Boolean(
        string='Дээд газраас ирсэн', default=False, groups="base.group_user")
    state = fields.Selection([
        ('draft', 'Боловсруулах'),
        ('confirm', 'Хянах'),
        ('validate1', 'Зөвшөөрсөн'),
        ('validate', 'Баталсан')],
        groups="base.group_user",
        default='draft',
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    coming_state = fields.Selection([
        ('conflict', 'Зөрчилтэй'),
        ('refuse', 'Буцаасан'),
        ('draft', 'Ирсэн'),
        ('receive', 'Хүлээн авсан'),
        ('transfer', 'Шилжүүлсэн'),
        ('review', 'Судлаж байгаа'),
        ('validate', 'Шийдвэрлэсэн')],
        groups="base.group_user",
        default='draft',
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    going_state = fields.Selection([
        ('draft', 'Бүртгэсэн'),
        ('sent', 'Илгээсэн')],
        groups="base.group_user",
        default='draft',
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    going_letters = fields.Many2one(
        'ubi.letter', string='Ирсэн бичгийн хариу', domain=[('letter_status', '=', 'going')], groups="base.group_user")
    coming_letters = fields.Many2one(
        'ubi.letter', string='Явсан бичгийн хариу', domain=[('letter_status', '=', 'coming')], groups="base.group_user")
    computed_letter_type_id = fields.Char(string='Баримтын төрөл', compute='_computed_letter_type_id')
    computed_letter_subject_id = fields.Char(string='Баримтын төрөл', compute='_computed_letter_subject_id')    
    computed_letter_desc = fields.Char(string='Агуулга', compute='_computed_letter_desc')   

    @api.onchange('letter_template_id')
    def _set_letter_template(self):
        if self.letter_template_text:
            self.custom_letter_template = self.letter_template_text

    @api.onchange('going_letters', 'coming_letters')
    def _computed_letter_type_id(self):
        _logger.info(self)
        if self.going_letters:
            self.follow_id = self.going_letters.id
            self.computed_letter_type_id = self.going_letters.letter_type_id.name
        elif self.coming_letters:
            self.follow_id = self.coming_letters.id
            self.computed_letter_type_id = self.coming_letters.letter_type_id.name

    @api.onchange('going_letters', 'coming_letters')
    def _computed_letter_subject_id(self):
        if self.going_letters:
            self.computed_letter_subject_id = self.going_letters.letter_subject_id.name
        elif self.coming_letters:
            self.computed_letter_subject_id = self.coming_letters.letter_subject_id.name

    @api.onchange('going_letters', 'coming_letters')
    def _computed_letter_desc(self):
        if self.going_letters:
            self.computed_letter_desc = self.going_letters.desc
        elif self.coming_letters:
            self.computed_letter_desc = self.coming_letters.desc


    @api.onchange('letter_number')
    def _set_letter_template1(self):
        if self.letter_template_id:
            string = self.custom_letter_template
            number = self.letter_number
            number_str = str(number)
            find0 = string.find("$number")
            asd = str("-1")

            if (str(find0) != asd):
                print(str(find0))
                self.custom_letter_template = string.replace(
                    "$number", number_str)
                string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$date", str((datetime.now()).strftime('%Y-%m-%d')))
                string = self.custom_letter_template
            else:
                self.custom_letter_template = self.letter_template_text
                string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$number", number_str)
                string = self.custom_letter_template
                if self.partner_id.name:
                    self.custom_letter_template = string.replace(
                        "$where", str(self.partner_id.name))
                    string = self.custom_letter_template
                if self.draft_user_id:
                    self.custom_letter_template = string.replace(
                        "$who", str(self.draft_user_id.name))
                    string = self.custom_letter_template
                if self.letter_subject_id.name:
                    self.custom_letter_template = string.replace(
                        "$terguu", str(self.letter_subject_id.name))
                    string = self.custom_letter_template
                if self.letter_total_num:
                    self.custom_letter_template = string.replace(
                        "$huudasni_too", str(self.letter_total_num))
                    string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$date", str((datetime.now()).strftime('%Y-%m-%d')))
                string = self.custom_letter_template





    @api.onchange('partner_id')
    def _set_letter_template2(self):
        if self.letter_template_id:
            string = self.custom_letter_template
            partner_id = self.partner_id.name
            partner_id_str = str(partner_id)
            find0 = string.find("$where")
            asd = str("-1")
            if (str(find0) != asd):
                self.custom_letter_template = string.replace(
                    "$where", partner_id_str)
                string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$date", str((datetime.now()).strftime('%Y-%m-%d')))
                string = self.custom_letter_template
            else:
                self.custom_letter_template = self.letter_template_text
                string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$where", str(self.partner_id.name))
                string = self.custom_letter_template
                if self.letter_number:
                    self.custom_letter_template = string.replace(
                        "$number", str(self.letter_number))
                    string = self.custom_letter_template
                if self.draft_user_id:
                    self.custom_letter_template = string.replace(
                        "$who", str(self.draft_user_id.name))
                    string = self.custom_letter_template
                if self.letter_subject_id.name:
                    self.custom_letter_template = string.replace(
                        "$terguu", str(self.letter_subject_id.name))
                    string = self.custom_letter_template
                if self.letter_total_num:
                    self.custom_letter_template = string.replace(
                        "$huudasni_too", str(self.letter_total_num))
                    string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$date", str((datetime.now()).strftime('%Y-%m-%d')))
                string = self.custom_letter_template


    @api.onchange('draft_user_id')
    def _set_letter_template3(self):
        if self.letter_template_id:
            string = self.custom_letter_template
            draft_user_id = self.draft_user_id.name
            draft_user_id_str = str(draft_user_id)
            find0 = string.find("$who")
            asd = str("-1")
            if (str(find0) != asd):
                self.custom_letter_template = string.replace(
                    "$who", draft_user_id_str)
                string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$date", str((datetime.now()).strftime('%Y-%m-%d')))
                string = self.custom_letter_template
            else:
                self.custom_letter_template = self.letter_template_text
                string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$who", draft_user_id_str)
                string = self.custom_letter_template
                if self.letter_number:
                    self.custom_letter_template = string.replace(
                        "$number", str(self.letter_number))
                    string = self.custom_letter_template
                if self.partner_id.name:
                    self.custom_letter_template = string.replace(
                        "$where", str(self.partner_id.name))
                    string = self.custom_letter_template
                if self.letter_subject_id.name:
                    self.custom_letter_template = string.replace(
                        "$terguu", str(self.letter_subject_id.name))
                    string = self.custom_letter_template
                if self.letter_total_num:
                    self.custom_letter_template = string.replace(
                        "$huudasni_too", str(self.letter_total_num))
                    string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$date", str((datetime.now()).strftime('%Y-%m-%d')))
                string = self.custom_letter_template

    @api.onchange('letter_subject_id')
    def _set_letter_template4(self):
        if self.letter_template_id:
            string = self.custom_letter_template
            letter_subject_id = self.letter_subject_id.name
            letter_subject_id_str = str(letter_subject_id)
            find0 = string.find("$terguu")
            asd = str("-1")
            if (str(find0) != asd):
                self.custom_letter_template = string.replace(
                    "$terguu", letter_subject_id_str)
                string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$date", str((datetime.now()).strftime('%Y-%m-%d')))
                string = self.custom_letter_template
            else:
                self.custom_letter_template = self.letter_template_text
                string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$terguu", letter_subject_id_str)
                string = self.custom_letter_template

                if self.letter_number:
                    self.custom_letter_template = string.replace(
                        "$number", str(self.letter_number))
                    string = self.custom_letter_template
                if self.partner_id.name:
                    self.custom_letter_template = string.replace(
                        "$where", str(self.partner_id.name))
                    string = self.custom_letter_template
                if self.draft_user_id:
                    self.custom_letter_template = string.replace(
                        "$who", str(self.draft_user_id.name))
                    string = self.custom_letter_template
                if self.letter_total_num:
                    self.custom_letter_template = string.replace(
                        "$huudasni_too", str(self.letter_total_num))
                    string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$date", str((datetime.now()).strftime('%Y-%m-%d')))
                string = self.custom_letter_template

    @api.onchange('letter_total_num')
    def _set_letter_template5(self):
        if self.letter_template_id:
            string = self.custom_letter_template
            letter_total_num = self.letter_total_num
            letter_total_num_str = str(letter_total_num)
            find0 = string.find("$huudasni_too")
            asd = str("-1")
            if (str(find0) != asd):
                self.custom_letter_template = string.replace(
                    "$huudasni_too", letter_total_num_str)
                string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$date", str((datetime.now()).strftime('%Y-%m-%d')))
                string = self.custom_letter_template
            else:
                self.custom_letter_template = self.letter_template_text
                string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$huudasni_too", letter_total_num_str)
                string = self.custom_letter_template

                if self.letter_number:
                    self.custom_letter_template = string.replace(
                        "$number", str(self.letter_number))
                    string = self.custom_letter_template
                if self.partner_id.name:
                    self.custom_letter_template = string.replace(
                        "$where", str(self.partner_id.name))
                    string = self.custom_letter_template
                if self.draft_user_id:
                    self.custom_letter_template = string.replace(
                        "$who", str(self.draft_user_id.name))
                    string = self.custom_letter_template
                if self.letter_subject_id.name:
                    self.custom_letter_template = string.replace(
                        "$terguu", str(self.letter_subject_id.name))
                    string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$date", str((datetime.now()).strftime('%Y-%m-%d')))
                string = self.custom_letter_template

    @api.model
    def create(self, vals):
        if vals.get('letter_status') == 'coming':
            vals['going_state'] = None
        elif vals.get('letter_status') == 'going':
            vals['coming_state'] = None    

        letter = super(UbiLetter, self).create(vals)

        return letter

    @api.model
    def check_connection_function(self, user):
        # try:
        #     _create_unverified_https_context = ssl._create_unverified_context
        # except AttributeError:
        #     pass
        # else:
        #     ssl._create_default_https_context = _create_unverified_https_context

        # ssl._create_default_https_context = ssl._create_unverified_context
        # ssl._create_default_https_context = ssl._create_stdlib_context
        # session = Session()
        # session.verify = False  # 'path/to/my/certificate.pem'
        # transport = Transport(session=session)

        # client = Client(
        #    'https://dev.docx.gov.mn/soap/api/api.wsdl', transport=transport)
        # get_list = getattr(client.service, 'get.org/list')
        # resp = get_list()
        # print(client)

        # HeaderMessage = client.factory.create('ns0:HeaderMessage')

        # Create a factory and assign the values
        data = """<Envelope xmlns = "http://schemas.xmlsoap.org/soap/envelope/" >
                    <Body>
                        <callRequest xmlns = "https://dev.docx.gov.mn/document/dto">
                            <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                            <service>get.org/list</service >
                            <params >{"name": "Таван толгой түлш"}</params>

                        </callRequest>
                    </Body>
                </Envelope>"""

        # result = client.service.call(data)
        # print(result)

        target_url = "https://dev.docx.gov.mn/soap/api"
        headers = {'Content-type': 'text/xml'}
        result = requests.post(target_url, data=data.encode(encoding='utf-8'),
                               headers=headers, verify=False)
        print(result.status_code)
        print(result.content)
        mytree = ET.fromstring(result.content)
       
        data = mytree.findall(".//callResponse")
        print(data)
        for node in data:
            print(node)

        return 'done'

    def letter_send_function(self):
        _logger.info(self)

    def action_sent(self):
        self.write({'going_state': 'sent'})

    def action_receive(self):
        self.write({'coming_state': 'receive'})

    def action_review(self):
        self.write({'coming_state': 'review'})

    def action_transfer(self):
        self.write({'coming_state': 'transfer'})

    def action_validate(self):
        self.write({'coming_state': 'validate'})

    def action_conflict(self):
        self.write({'coming_state': 'conflict'})

    def action_refuse(self):
        self.write({'coming_state': 'refuse'})

    @api.model
    def _compute_going_letter_response(self):
        going_letters = self.env['ubi.letter'].search([('letter_status', '=', 'going')])
        _logger.info(going_letters)
        self.going_letters = going_letters

    def _compute_coming_letter_response(self):
        coming_letters = self.env['ubi.letter'].search([('letter_status', '=', 'coming')])
        self.coming_letters = coming_letters