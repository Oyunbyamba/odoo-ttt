# -*- coding: utf-8 -*-
import logging
from odoo import models, tools, fields, api, _
from datetime import date, datetime, timedelta, time
import os
import json
import base64
import xml.etree.ElementTree as ET
import re
import ssl
import requests
from bs4 import BeautifulSoup
from odoo.exceptions import ValidationError, AccessError, UserError

_logger = logging.getLogger(__name__)


class UbiLetterGoing(models.Model):
    _name = "ubi.letter.going"
    _inherit = ['ubi.letter', 'mail.thread', 'mail.activity.mixin']
    _description = " Явсан бичиг"
    _rec_name = 'letter_number'
    _mail_post_access = 'read'

    follow_id = fields.Many2one('ubi.letter.coming', groups="base.group_user")
    letter_attachment_ids = fields.Many2many(
        'ir.attachment', 'letter_going_doc_attach', 'letter_id', 'doc_id', string="Хавсралт", copy=False)
    state = fields.Selection([
        ('draft', 'Бүртгэсэн'),
        ('confirm', 'Хянасан'),
        ('validate1', 'Зөвшөөрсөн'),
        ('validate', 'Баталсан'),
        ('expected', 'Хүлээгдэж буй'),
        ('sent', 'Илгээсэн'),
        ('received', 'Хүлээн авсан'),
        ('refuse', 'Цуцласан')],
        groups="base.group_user",
        default='draft',
        string='Явсан бичгийн төлөв', store=True, readonly=True, copy=False, tracking=True)
    send_date = fields.Date(
        string='Илгээсэн огноо', groups="base.group_user")
    coming_letters = fields.Many2one(
        'ubi.letter.coming', string='Ирсэн дугаар', groups="base.group_user")
    letter_template_id = fields.Many2one(
        'ubi.letter.template', string='Баримтын загвар', groups="base.group_user")
    letter_template_text = fields.Html(
        'Агуулга', groups="base.group_user")
    custom_letter_template = fields.Html('Template', groups="base.group_user")
    paper_size = fields.Selection(
        'Paper size', related="letter_template_id.paper_size")

    def _set_custom_template(self):
        if self.custom_letter_template:
            self.custom_letter_template = self.custom_letter_template

    def replace_template_text(self, key_word, val):
        template_text = self.custom_letter_template
        soup = BeautifulSoup(template_text, 'html.parser')
        match = soup.find('span', {'id': key_word})
        match.string = val
        # match.contents = val

        # _logger.info(match)
        self.custom_letter_template = soup

    @api.onchange('letter_template_id')
    def _compute_letter_template(self):
        self.custom_letter_template = ''
        if self.letter_template_id:
            if self.letter_template_id.paper_size == 'a4':
                report = self.env['ir.actions.report']._get_report_from_name(
                    'ubisol_letters.letter_detail_report_a4')
            elif self.letter_template_id.paper_size == 'a5':
                report = self.env['ir.actions.report']._get_report_from_name(
                    'ubisol_letters.letter_detail_report_a5')

            data = {'letter_template_text': self.letter_template_text}
            html = report.render_qweb_html(self.id, data=data)[0]
            self.custom_letter_template = html
            if self.letter_number:
                self.replace_template_text('letter_number', self.letter_number)

            if self.letter_subject_id:
                self.replace_template_text(
                    'subject', self.letter_subject_id.name)

    @api.onchange('letter_number')
    def _compute_letter_template1(self):
        if self.letter_template_id and self.letter_number:
            self.replace_template_text('letter_number', self.letter_number)

    @api.onchange('letter_subject_id')
    def _compute_letter_template2(self):
        if self.letter_template_id and self.letter_subject_id:
            self.replace_template_text('subject', self.letter_subject_id.name)

    @api.onchange('letter_template_text')
    def _compute_letter_template3(self):
        if self.letter_template_id:
            if self.letter_template_id.paper_size == 'a4':
                report = self.env['ir.actions.report']._get_report_from_name(
                    'ubisol_letters.letter_detail_report_a4')
            elif self.letter_template_id.paper_size == 'a5':
                report = self.env['ir.actions.report']._get_report_from_name(
                    'ubisol_letters.letter_detail_report_a5')

            data = {'letter_template_text': self.letter_template_text}
            html = report.render_qweb_html(self.id, data=data)[0]
            self.custom_letter_template = html

    @api.onchange('coming_letters')
    def _computed_letter_type(self):
        self.computed_letter_type = ''
        if self.coming_letters:
            self.follow_id = self.coming_letters.id
            self.computed_letter_type = self.coming_letters.letter_type_id.name if self.coming_letters.letter_type_id else ''

    @api.onchange('coming_letters')
    def _computed_letter_subject(self):
        self.computed_letter_subject = ''
        if self.coming_letters:
            self.computed_letter_subject = self.coming_letters.letter_subject_id.name if self.coming_letters.letter_subject_id else ''

    @api.onchange('coming_letters')
    def _computed_letter_desc(self):
        self.computed_letter_desc = ''
        if self.coming_letters:
            self.computed_letter_desc = self.coming_letters.desc

    @api.model
    def create(self, vals):
        letter = super(UbiLetterGoing, self).create(vals)

        return letter

    def write(self, vals):
        letter = super(UbiLetterGoing, self).write(vals)

        return letter

    def print_report(self):
        if self.ids:
            report = self.env.ref('ubisol_letters.letter_detail_report_a5_pdf')
            return report.report_action(self.ids)

    def action_sent(self):
        self.write({'state': 'sent'})

    def prepare_sending(self):
        letters = self.env['ubi.letter.going'].browse(self.ids)
        for letter in letters:
            if any(letter.state not in ['expected'] for letter in self):
                raise UserError(
                    _('Зөвхөн хүлээгдэж буй төлөвтэй баримтыг "Илгээх" төлөвт оруулах боломжтой.'))

            if letter.state == 'expected':
                request_data = self.build_state_doc(letter)
                result = self.send_letter(request_data)
                if result['status'] == '200':
                    data = result['data']
                    letter.write(
                        {"state": "sent", "tabs_id": data['id'], "send_date": datetime.today().strftime('%Y-%m-%d')})
                else:
                    raise UserError(_(result['data']))
        return {}

    def build_state_doc(self, letter):
        body = {}
        body['documentDate'] = datetime.strftime(
            letter.letter_date, '%Y-%m-%d') if letter.letter_date else ''
        body['documentTypeId'] = letter.letter_type_id.id if letter.letter_type_id.id == 1 else 2
        body['documentNumber'] = letter.letter_number or ''
        body['documentName'] = letter.letter_subject_id.name or ''
        body['signName'] = letter.validate_user_id.name or ''
        # body['orgId'] = letter.partner_id.id_by_state
        orgList = []
        for part_id in letter.partner_id:
            partner = {}
            partner['orgId'] = part_id.ubi_letter_org_id
            orgList.append(partner)

        body['orgList'] = orgList
        # body['orgName'] = letter.partner_id.name
        body['fileList'] = self.prepare_files(letter)
        # ? shalgaj hariu bichig mun esehiig medne
        body['isReplyDoc'] = True if letter.follow_id else False
        body['isNeedReply'] = letter.must_return
        # datetime.strftime(letter.letter_date, '%Y-%m-%d') if letter.letter_date else ''
        body['priorityId'] = letter.priority_id
        body['noOfPages'] = letter.letter_total_num
        body['responseTypeID'] = 1  # letter.must_return  # nuhtsul shalgah
        # mistyped asuuh heregtei
        body['responseDate'] = datetime.strftime(
            letter.must_return_date, '%Y-%m-%d') if letter.must_return_date else ''
        # 1 #letter.follow_id.letter_number or ''
        body['srcDocumentNumber'] = letter.follow_id.letter_number if letter.follow_id else ''
        # body['srcDocumentCode'] = letter.follow_id.tabs_id if letter.follow_id else ''
        body['srcDocumentDate'] = datetime.strftime(
            letter.follow_id.letter_date, '%Y-%m-%d') if letter.follow_id and letter.follow_id.letter_date else ''

        json_data = json.dumps(body)
        return json_data

    def prepare_files(self, letter):

        files = letter.letter_attachment_ids
        file_array = []
        for file in files:
            fileList = {}
            fileList['name'] = file.name
            fileList['size'] = file.file_size
            fileList['type'] = file.mimetype

            fileList['data'] = file.datas.decode()
            file_array.append(fileList)
        return file_array

    @api.model
    def send_letter(self, request_data):
        template = """<Envelope xmlns = "http://schemas.xmlsoap.org/soap/envelope/" >
                        <Body>
                            <callRequest xmlns = "https://docx.gov.mn/document/dto">
                                <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                                <service>post.public.document</service >
                                <params >%s</params>
                            </callRequest>
                        </Body>
                    </Envelope>"""

        data = template % (request_data)
        target_url = "https://docx.gov.mn/soap/api"
        headers = {'Content-type': 'text/xml'}
        result = requests.post(target_url, data=data.encode(encoding='utf-8'),
                               headers=headers, verify=False)
        mytree = ET.fromstring(result.content)

        status = mytree.find(
            './/{https://dev.docx.gov.mn/document/dto}responseCode')
        find = mytree.find(
            './/{https://dev.docx.gov.mn/document/dto}data')
        msg = mytree.find(
            './/{https://dev.docx.gov.mn/document/dto}responseMessage')

        if(status.text.strip() == '200'):
            data = json.loads(find.text.strip())
            return {'status': status.text.strip(), 'data': data}
        else:
            return {'status': status.text.strip(), 'data': msg.text.strip()}

    def cancel_sending(self):
        if len(self.ids) >= 1:
            letters = self.env['ubi.letter.going'].browse(self.ids)
            for letter in letters:
                if any(letter.state not in ['sent'] for letter in self):
                    raise UserError(
                        _('Зөвхөн илгээсэн төлөвтэй баримтыг "Цуцлах" төлөвт оруулах боломжтой.'))

                if letter.state == 'sent':
                    result = self.cancel_sent(letter)
                    if result['status'] == '200':
                        letter.write({"state": 'refuse'})
                    else:
                        raise UserError(_(result['data']))

        return {}

    @api.model
    def cancel_sent(self, letter):
        # {"id":381,"cancelPerson":"Бат","cancelPosition":"Бичиг хэрэг","cancelComment":"Ирсэн бичгийн материал дутуу учир буцаалаа шүү хахаха"}
        params = {"id": letter.tabs_id}
        template = """<Envelope xmlns = "http://schemas.xmlsoap.org/soap/envelope/" >
                    <Body>
                        <callRequest xmlns = "https://docx.gov.mn/document/dto">
                            <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                            <service>post.public.document/delete</service >
                            <params>%s</params>

                        </callRequest>
                    </Body>
                </Envelope>"""
        data = template % params
        target_url = "https://docx.gov.mn/soap/api"
        headers = {'Content-type': 'text/xml'}
        result = requests.post(target_url, data=data.encode(
            encoding='utf-8'), headers=headers, verify=False)
        if result.status_code == 200:

            mytree = ET.fromstring(result.content)

            status = mytree.find(
                './/{https://dev.docx.gov.mn/document/dto}responseCode')
            find = mytree.find(
                './/{https://dev.docx.gov.mn/document/dto}data')
            msg = mytree.find(
                './/{https://dev.docx.gov.mn/document/dto}responseMessage')

            if(status.text.strip() == '200'):
                return {'status': status.text.strip(), 'data': []}
            else:
                return {'status': status.text.strip(), 'data': msg.text.strip()}
        else:
            return {'status': 'ERROR', 'data': 'Сүлжээний алдаа гарлаа.'}
