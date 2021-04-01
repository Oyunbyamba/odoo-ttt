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

    def _get_default_note(self):
        result = """
            <div>
                <p class="terms">Payment terms are</p>
                <ul><li>15% in advance</li><ul/>
            </div>"""

        return result
    follow_id = fields.Many2one('ubi.letter', groups="hr.group_hr_user")
    draft_user_id = fields.Many2one('res.users', groups="hr.group_hr_user")
    validate_user_id = fields.Many2one('res.users', groups="hr.group_hr_user")
    confirm_user_id = fields.Many2one('res.users', groups="hr.group_hr_user")
    letter_attachment_id = fields.Many2many(
        'ir.attachment', 'letter_doc_attach', 'letter_id', 'doc_id', string="Хавсралт", copy=False)

    is_local = fields.Boolean(string='Дотоод бичиг', groups="hr.group_hr_user")
    letter_status = fields.Selection([
        ('coming', 'Ирсэн'),
        ('going', 'Явсан'),
        ('planning', 'Төлөвлөлт')],
        groups="hr.group_hr_user",
        string='Төлөв', store=True, readonly=True, copy=False, tracking=True)
    card_number = fields.Integer(
        string='Картын дугаар', help="Картын дугаар", groups="hr.group_hr_user")
    letter_number = fields.Integer(
        string='Бичгийн дугаар', help="Бичгийн дугаар", groups="hr.group_hr_user")
    register_number = fields.Integer(
        string='Бүртгэлийн дугаар', help="Бүртгэлийн дугаар", groups="hr.group_hr_user")
    letter_total_num = fields.Integer(
        string='Хуудасны тоо', help="Хуудасны тоо", groups="hr.group_hr_user")
    desc = fields.Char(string='Товч утга', groups="hr.group_hr_user")
    received_date = fields.Date(
        string='Хүлээн авсан огноо', groups="hr.group_hr_user")
    registered_date = fields.Date(
        string='Бүртгэсэн огноо', groups="hr.group_hr_user")
    return_date = fields.Date(
        string='Шийдвэрлэх огноо', groups="hr.group_hr_user")
    letter_date = fields.Date(string='Бичгийн огноо',
                              groups="hr.group_hr_user")

    partner_id = fields.Many2many(
        'res.partner', string='Хаанаас', groups="hr.group_hr_user")
    letter_type_id = fields.Many2one(
        'ubi.letter.type', string='Бичгийн төрөл', groups="hr.group_hr_user")
    letter_subject_id = fields.Many2one(
        'ubi.letter.subject', string='Бичгийн тэргүү', groups="hr.group_hr_user")
    letter_template_id = fields.Many2one(
        'ubi.letter.template', string='Бичгийн загвар', groups="hr.group_hr_user")
    letter_template_text = fields.Html(
        related="letter_template_id.letter_template", groups="hr.group_hr_user")
    custom_letter_template = fields.Html(
        'Custom text', groups="hr.group_hr_user", default=_get_default_note)
    department_id = fields.Many2one(
        'hr.department', string='Хариуцах Хэлтэс', groups="hr.group_hr_user")
    user_id = fields.Many2one(
        'res.users', string='Хэнд', groups="hr.group_hr_user")

    must_return = fields.Boolean(
        string='Хариу өгөх', default=False, groups="hr.group_hr_user")
    is_head_company = fields.Boolean(
        string='Дээд газраас ирсэн', default=False, groups="hr.group_hr_user")
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

    @api.onchange('letter_number')
    def _set_letter_template1(self):
        if self.custom_letter_template:
            string = self.custom_letter_template
            number = self.letter_number
            number_str = str(number)
            find0 = string.find("$number")
            asd = str("-1")
            if (str(find0) != asd):
                print(str(find0))
                self.custom_letter_template = string.replace(
                    "$number", number_str)
                print("unen")
            else:
                self.custom_letter_template = self.letter_template_text
                string = self.custom_letter_template
                self.custom_letter_template = string.replace(
                    "$number", number_str)
                print("hudal")

    @api.onchange('partner_id')
    def _set_letter_template3(self):
        if self.custom_letter_template:
            string = self.custom_letter_template
            partner_id = self.partner_id.name
            partner_id_str = str(partner_id)
            self.custom_letter_template = string.replace(
                "$where", partner_id_str)

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
        mytree.get_root()
        data = mytree.findall(".//callResponse")
        print(data)
        for node in data:
            print(node)

        return 'done'


# class CustomTransport(HttpAuthenticated):

#     def u2handlers(self):

#         # use handlers from superclass
#         handlers = HttpAuthenticated.u2handlers(self)

#         # create custom ssl context, e.g.:
#         ctx = ssl.create_default_context(cafile="/home/odoo/fullchain.pem")
#         # configure context as needed...
#         ctx.check_hostname = False

#         # add a https handler using the custom context
#         handlers.append(HTTPSHandler(context=ctx))
#         return handlers
