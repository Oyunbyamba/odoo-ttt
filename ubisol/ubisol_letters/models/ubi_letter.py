# -*- coding: utf-8 -*-
import logging
from odoo import models, tools, fields, api
from datetime import date, datetime, timedelta, time
import os
import json
import base64
import xml.etree.ElementTree as ET
import re
import ssl
import requests

_logger = logging.getLogger(__name__)


class UbiLetter(models.Model):
    _name = "ubi.letter"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = " "
    _rec_name = 'letter_number'

    def _get_default_note(self):
        result = """"""
        return result

    letter_attachment_ids = fields.Many2many(
        'ir.attachment', 'letter_doc_attach', 'letter_id', 'doc_id', string="Хавсралт", copy=False)

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
    letter_date = fields.Date(string='Баримтын огноо', default=datetime.today(),
                              groups="base.group_user")
    processing_datetime = fields.Datetime(string='Явцын огноо',
                                          default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), groups="base.group_user")
    # partner_ids = fields.Many2many(
    #     'res.partner', string='Хаанаас', groups="base.group_user")
    partner_id = fields.Many2one(
        'res.partner', string='Хаанаас', domain=[('ubi_letter_org', '=', True)], groups="base.group_user")
    user_id = fields.Many2one('res.users', string='Хэнд')
    official_person = fields.Char('Албан тушаалтан', groups="base.group_user")
    follow_id = fields.Many2one('ubi.letter', groups="base.group_user")
    draft_user_id = fields.Many2one('res.users', groups="base.group_user")
    confirm_user_id = fields.Many2one('res.users', groups="base.group_user")
    validate_user_id = fields.Many2one('res.users', groups="base.group_user")


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
    
    must_return = fields.Boolean(
        string='Хариутай эсэх', default=False, groups="base.group_user")
    is_reply_doc = fields.Boolean(
        string='Хариу бичсэн эсэх', default=False, groups="base.group_user")    
    is_local = fields.Boolean(
        string='Дотоод бичиг', groups="base.group_user", default=False)    
    is_head_company = fields.Boolean(
        string='Дээд газраас ирсэн', default=False, groups="base.group_user")
    tabs_id = fields.Integer('Tabs id', groups="base.group_user")    
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
        ('sent', 'Илгээсэн'),
        ('cancel', 'Цуцлах'),
        ('refuse', 'Буцаагдсан')],
        groups="base.group_user",
        default='draft',
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    going_letters = fields.Many2one(
        'ubi.letter', string='Ирсэн дугаар', domain=[('letter_status', '=', 'going')], groups="base.group_user")
    coming_letters = fields.Many2one(
        'ubi.letter', string='Явсан бичгийн дугаар', domain=[('letter_status', '=', 'coming')], groups="base.group_user")
    computed_letter_type = fields.Char(
        string='Баримтын төрөл', compute='_computed_letter_type', groups="base.group_user")
    computed_letter_subject = fields.Char(
        string='Баримтын төрөл', compute='_computed_letter_subject', groups="base.group_user")
    computed_letter_desc = fields.Char(
        string='Агуулга', compute='_computed_letter_desc', groups="base.group_user")

    @api.onchange('letter_template_id')
    def _set_letter_template(self):
        if self.letter_template_text:
            self.custom_letter_template = self.letter_template_text

    @api.onchange('going_letters', 'coming_letters')
    def _computed_letter_type(self):
        self.computed_letter_type = ''
        if self.going_letters:
            self.follow_id = self.going_letters.id
            self.computed_letter_type = self.going_letters.letter_type_id.name if self.going_letters.letter_type_id else ''
        elif self.coming_letters:
            self.follow_id = self.coming_letters.id
            self.computed_letter_type = self.coming_letters.letter_type_id.name if self.coming_letters.letter_type_id else ''

    @api.onchange('going_letters', 'coming_letters')
    def _computed_letter_subject(self):
        self.computed_letter_subject = ''
        if self.going_letters:
            self.computed_letter_subject = self.going_letters.letter_subject_id.name if self.going_letters.letter_subject_id else ''
        elif self.coming_letters:
            self.computed_letter_subject = self.coming_letters.letter_subject_id.name if self.coming_letters.letter_subject_id else ''

    @api.onchange('going_letters', 'coming_letters')
    def _computed_letter_desc(self):
        self.computed_letter_desc = ''
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

    def write(self, vals):
        _logger.info(vals)
        letter = super(UbiLetter, self).write(vals)

    def letter_send_function(self):
        selected_ids = self.env.context.get('active_ids', [])
        self.prepare_sending(selected_ids)

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
    def prepare_sending(self, ids):
        letters = self.env['ubi.letter'].browse(ids)
        for letter in letters:
            request_data = self.build_state_doc(letter)
            self.send_letter(request_data)

    def build_state_doc(self, letter):
        body = {}
        body['documentDate'] = datetime.strftime(
            letter.letter_date, '%Y-%m-%d') if letter.letter_date else ''
        body['documentTypeId'] = 1  # letter.letter_type_id.id or ''
        body['documentNumber'] = letter.letter_number or ''
        body['documentName'] = letter.letter_subject_id.name or ''
        body['signName'] = letter.validate_user_id.name or ''
        # body['OrgCode'] = letter.partner_id.code_by_state
        body['OrgCode'] = 0
        # body['orgId'] = letter.partner_id.id_by_state
        body['orgId'] = 447
        # body['orgName'] = letter.partner_id.name
        body['orgName'] = 'Газрын шинэтгэлийн үндэсний хороо'
        body['fileList'] = self.prepare_files(letter)
        # ? shalgaj hariu bichig mun esehiig medne
        body['isReplyDoc'] = 0
        body['isNeedReply'] = letter.must_return
        # datetime.strftime(letter.letter_date, '%Y-%m-%d') if letter.letter_date else ''
        body['createdUserId'] = 5466
        body['priorityId'] = 0
        body['noOfPages'] = letter.letter_total_num
        body['responseTypeID'] = 1  # letter.must_return  # nuhtsul shalgah
        # mistyped asuuh heregtei
        body['responceDate'] = datetime.strftime(
            letter.must_return_date, '%Y-%m-%d') if letter.must_return_date else ''
        # 1 #letter.follow_id.letter_number or ''
        body['srcDocumentNumber'] = ''
        body['srcDocumentCode'] = ''
        body['srcDocumentDate'] = datetime.strftime(
            letter.follow_id.letter_date, '%Y-%m-%d') if letter.follow_id and letter.follow_id.letter_date else ''

        json_data = json.dumps(body)
        return json_data

    def download_files(self, letter):

        files = letter.letter_attachment_ids
        file_array = []
        for file in files:
            fileList = {}
            fileList['name'] = file.name
            fileList['size'] = file.file_size
            fileList['type'] = file.mimetype
            path = file._full_path(file.store_fname)
           # with tools.file_open(path, 'rb') as file_binary:
            # content = file.datas
            # fileList['data'] = base64.b64encode(content)
            fileList['data'] = "aGVsbG8="
            file_array.append(fileList)
        return file_array

    @api.model
    def send_letter(self, request_data):
        _logger.info(request_data)
        template = """<Envelope xmlns = "http://schemas.xmlsoap.org/soap/envelope/" >
                        <Body>
                            <callRequest xmlns = "https://dev.docx.gov.mn/document/dto">
                                <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                                <service>post.public.document</service >
                                <params >%s</params>
                            </callRequest>
                        </Body>
                    </Envelope>"""

        data = template % (request_data)

        _logger.info(data)

        target_url = "https://dev.docx.gov.mn/soap/api"
        headers = {'Content-type': 'text/xml'}
        result = requests.post(target_url, data=data.encode(encoding='utf-8'),
                               headers=headers, verify=False)
        print(result.status_code)
        print(result.content)

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

        # # Create a factory and assign the values
        data = """<Envelope xmlns = "http://schemas.xmlsoap.org/soap/envelope/" >
                    <Body>
                        <callRequest xmlns = "https://dev.docx.gov.mn/document/dto">
                            <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                            <service>get.document_list/list</service >
                            <params>{statusId : 1}</params>

                        </callRequest>
                    </Body>
                </Envelope>"""

        # result = client.service.call(data)
        # print(result)

        target_url = "https://dev.docx.gov.mn/soap/api"
        headers = {'Content-type': 'text/xml'}
        result = requests.post(target_url, data=data.encode(
            encoding='utf-8'), headers=headers, verify=False)
        # print(result.status_code)
        # print(result.content)
        mytree = ET.fromstring(result.content)

        status = mytree.find(
            './/{https://dev.docx.gov.mn/document/dto}responseCode')

        if(status.text.strip() == '200'):
            find = mytree.find(
                './/{https://dev.docx.gov.mn/document/dto}data')

            data = json.loads(find.text.strip())
            for doc in data:
                already_received = self.env['ubi.letter'].search(
                    [('letter_number', '=', doc['documentNumber']), ('partner_id.orgId', '=', doc['orgId']), ('letter_status', '=', 'coming')], limit=1)
                # umnu orj irseng shalgah
                if(already_received):
                    pass
                else:
                    vals = self.prepare_receiving(doc)
                    self.env['ubi.letter'].create(vals)
        else:
            print("FALSE")

        return {}

    def prepare_receiving(self, doc):
        vals = {}

        vals['letter_date'] = doc['documentDate']
        vals['letter_type_id'] = doc['documentTypeId'] = 1
        vals['letter_number'] = doc['documentNumber']
        vals['letter_subject_id'] = doc['documentName']
        vals['validate_user_id'] = doc['signName']
        # body['orgId'] = letter.partner_id.id_by_state
        vals['orgId'] = doc['orgId']
        # body['orgName'] = letter.partner_id.name
        vals['orgName'] = doc['orgName']
        vals['isReplyDoc'] = body['isReplyDoc']
        vals['must_return'] = body['isNeedReply']
        # datetime.strftime(letter.letter_date, '%Y-%m-%d') if letter.letter_date else ''
        vals['createdUserId'] = body['createdUserId']
        vals['priorityId'] = body['priorityId']

        # ? shalgaj hariu bichig mun esehiig medne

        vals['letter_total_num'] = doc['noOfPages']
        # mistyped asuuh heregtei
        doc['srcDocumentNumber']
        doc['srcDocumentCode']
        doc['srcDocumentDate']
        vals['letter_attachment_ids'] = self.download_files(doc['fileList'])
        vals['coming_state'] = 'draft'
        vals['letter_status'] = 'coming'

        return vals

    def download_files(self, files):
        attachment_ids = []
        for file in files:
            file_url = file['url']
            file_name = file['name']
            result = base64.b64encode(requests.get(file_url.strip()).content).replace(b'\n', b'')
            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': result,
                'res_model': 'ubi.letter'
            })
            attachment_ids.append(attachment)

        attachment_ids = [[6, False, attachment_ids]]

        return attachment_ids
