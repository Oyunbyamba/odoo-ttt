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
from odoo.exceptions import ValidationError, AccessError, RedirectWarning

_logger = logging.getLogger(__name__)


class UbiLetterComing(models.Model):
    _name = "ubi.letter.coming"
    _inherit = ['ubi.letter', 'mail.thread', 'mail.activity.mixin']
    _description = " "
    _rec_name = 'letter_number'

    letter_attachment_ids = fields.Many2many(
        'ir.attachment', 'letter_coming_doc_attach', 'letter_id', 'doc_id', string="Хавсралт", copy=False)
    state = fields.Selection([
        ('conflict', 'Зөрчилтэй'),
        ('refuse', 'Буцаасан'),
        ('draft', 'Ирсэн'),
        ('receive', 'Хүлээн авсан'),
        ('transfer', 'Шилжүүлсэн'),
        ('review', 'Судлаж байгаа'),
        ('validate', 'Шийдвэрлэсэн')],
        groups="base.group_user",
        default='draft',
        string='Ирсэн бичгийн төлөв', store=True, readonly=True, copy=False, tracking=True)
    going_letters = fields.Many2one(
        'ubi.letter.going', string='Явсан бичгийн дугаар', groups="base.group_user")

    def call_return_wizard(self):
        if len(self.ids) >= 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Ирсэн бичиг буцаах'),
                'res_model': 'letter.return.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'active_ids': self.ids},
                'views': [[False, 'form']]
            }
        return {}

    @api.onchange('letter_template_id')
    def _set_letter_template(self):
        if self.letter_template_text:
            self.custom_letter_template = self.letter_template_text

    @api.onchange('going_letters')
    def _computed_letter_type(self):
        self.computed_letter_type = ''
        if self.going_letters:
            self.follow_id = self.going_letters.id
            self.computed_letter_type = self.going_letters.letter_type_id.name if self.going_letters.letter_type_id else ''

    @api.onchange('going_letters')
    def _computed_letter_subject(self):
        self.computed_letter_subject = ''
        if self.going_letters:
            self.computed_letter_subject = self.going_letters.letter_subject_id.name if self.going_letters.letter_subject_id else ''

    @api.onchange('going_letters')
    def _computed_letter_desc(self):
        self.computed_letter_desc = ''
        if self.going_letters:
            self.computed_letter_desc = self.going_letters.desc

    @api.model
    def create(self, vals):
        letter = super(UbiLetterComing, self).create(vals)

        return letter

    def write(self, vals):
        letter = super(UbiLetterComing, self).write(vals)

        return letter

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
    def check_new_letters(self, user):
        data = """<Envelope xmlns = "http://schemas.xmlsoap.org/soap/envelope/" >
                    <Body>
                        <callRequest xmlns = "https://dev.docx.gov.mn/document/dto">
                            <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                            <service>get.document_list/list</service >
                            <params>{}</params>

                        </callRequest>
                    </Body>
                </Envelope>"""

        # result = client.service.call(data)
        # print(result)

        target_url = "https://dev.docx.gov.mn/soap/api"
        headers = {'Content-type': 'text/xml'}
        result = requests.post(target_url, data=data.encode(
            encoding='utf-8'), headers=headers, verify=False)

        mytree = ET.fromstring(result.content)

        status = mytree.find(
            './/{https://dev.docx.gov.mn/document/dto}responseCode')

        if(status.text.strip() == '200'):
            find = mytree.find(
                './/{https://dev.docx.gov.mn/document/dto}data')

            data = json.loads(find.text.strip())
            count = 0
            for doc in data:
                already_received = self.env['ubi.letter'].search(
                    [('letter_number', '=', doc['documentNumber']), ('partner_id.ubi_letter_org_id', '=', doc['orgId'])], limit=1)
                # umnu orj irseng shalgah
                if(already_received):
                    pass
                else:
                    vals = self.prepare_receiving(doc)
                    self.env['ubi.letter'].create(vals)
                    count += 1
            return 'Шинээр нийт ' + str(count) + ' бичиг ирсэн байна.'

        else:
            return 'Албан бичиг татах системтэй холбогдох явцад алдаа гарлаа.'

        return {}

    def prepare_receiving(self, doc):
        vals = {}
        vals['letter_date'] = doc['documentDate'] if 'documentDate' in doc else datetime.strftime(
            datetime.today(), '%Y-%m-%d')
        vals['tabs_id'] = doc['id'] if 'id' in doc else ''
        vals['letter_type_id'] = doc['documentTypeId'] if 'documentTypeId' in doc else ''
        vals['letter_number'] = doc['documentNumber'] if 'documentNumber' in doc else ''
        vals['letter_subject_id'] = self.check_subject(
            doc['documentName']) if 'documentName' in doc else ''
        vals['official_person'] = doc['signName'] if 'signName' in doc else ''

        vals['partner_id'] = self.check_partners(doc).id or ''
        vals['is_reply_doc'] = doc['isReplyDoc'] if 'isReplyDoc' in doc else ''
        vals['must_return'] = doc['isNeedReply'] if 'isNeedReply' in doc else ''
        # datetime.strftime(letter.letter_date, '%Y-%m-%d') if letter.letter_date else ''
        vals['priority_id'] = str(
            doc['priorityId']) if 'priorityId' in doc and doc['priorityId'] > 0 else '1'

        # ? shalgaj hariu bichig mun esehiig medne

        vals['letter_total_num'] = doc['noOfPages'] if doc['noOfPages'] else ''
        # mistyped asuuh heregtei
        vals['src_document_number'] = doc['srcDocumentNumber'] if 'srcDocumentNumber' in doc else ''
        vals['src_document_code'] = doc['srcDocumentCode'] if 'srcDocumentCode' in doc else ''
        vals['src_document_date'] = doc['srcDocumentDate'] if 'srcDocumentDate' in doc else ''
        vals['letter_attachment_ids'] = self.download_files(
            doc['fileList']) if len(doc['fileList']) > 0 else []
        vals['coming_state'] = 'draft'

        return vals

    def download_files(self, files):
        attachment_ids = []
        for file in files:
            file_url = "https://dev.docx.gov.mn"+file['url']
            file_name = file['name']
            result = base64.b64encode(requests.get(
                file_url.strip(), verify=False).content).replace(b'\n', b'')
            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': result,
                'res_model': 'ubi.letter'
            })
            attachment_ids.append(attachment.id)

        attachment_ids = [[6, False, attachment_ids]]

        return attachment_ids

    def check_partners(self, doc):

        partner = self.env['res.partner'].search(
            [('ubi_letter_org_id', '=', doc['orgId'])], limit=1)
        if not partner:
            vals = {}
            vals['ubi_letter_org_id'] = doc['orgId']
            vals['name'] = doc['orgName']
            vals['ubi_letter_org'] = True
            vals['is_company'] = True
            partner = self.env['res.partner'].create(vals)
        else:
            partner
        return partner

    def check_subject(self, name):
        subject = self.env['ubi.letter.subject'].search(
            [('name', 'ilike', name)], limit=1)
        if not subject:
            subject = self.env['ubi.letter.subject'].create({"name": name})
        return subject.id

    @api.model
    def return_receiving(self, ids, wizard_vals):
        letters = self.env['ubi.letter'].browse(ids)
        for letter in letters:
            if letter.coming_state == 'receive':
                params = {"id": letter.tabs_id, "cancelPerson": wizard_vals.cancel_employee.name, "cancelPosition": wizard_vals.cancel_position,
                          "cancelComment": wizard_vals.cancel_comment}
                result = self.return_received(params)
                if result:
                    letter.write({"coming_state": "refuse",
                                  "cancel_comment": wizard_vals.cancel_comment,
                                  "cancel_position": wizard_vals.cancel_position,
                                  "cancel_employee": wizard_vals.cancel_employee.name
                                  })
        return True

    def return_received(self, params):

        template = """<Envelope xmlns = "http://schemas.xmlsoap.org/soap/envelope/" >
                    <Body>
                        <callRequest xmlns = "https://dev.docx.gov.mn/document/dto">
                            <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                            <service>post.public.document/cancel</service >
                            <params>%s</params>

                        </callRequest>
                    </Body>
                </Envelope>"""
        data = template % params
        target_url = "https://dev.docx.gov.mn/soap/api"
        headers = {'Content-type': 'text/xml'}
        result = requests.post(target_url, data=data.encode(
            encoding='utf-8'), headers=headers, verify=False)

        if result.status_code == 200:

            mytree = ET.fromstring(result.content)

            status = mytree.find(
                './/{https://dev.docx.gov.mn/document/dto}responseCode')
            find = mytree.find(
                './/{https://dev.docx.gov.mn/document/dto}responseMessage')
            data = find.text.strip()
            if(status.text.strip() == '200'):
                return {'status': 200}
            else:
                return {'status': status.text.strip(), 'data': data}
        else:
            return {'status': 'ERROR', 'data': 'Сүлжээний алдаа гарлаа.'}

    def letter_receiving(self):

        letters = self.env['ubi.letter'].browse(ids)
        for letter in letters:
            if letter.coming_state == 'draft':
                params = {"id": letter.tabs_id,
                          "receivePerson": "D.Bold", "receivePosition": "Darga"}
                result = self.letter_received(params)
                if result:
                    letter.write({"coming_state": "receive"})
        return True

    def letter_received(self, params):

        template = """<Envelope xmlns = "http://schemas.xmlsoap.org/soap/envelope/" >
                    <Body>
                        <callRequest xmlns = "https://dev.docx.gov.mn/document/dto">
                            <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                            <service>post.public.document/receive</service >
                            <params>%s</params>
                        </callRequest>
                    </Body>
                </Envelope>"""
        data = template % params
        target_url = "https://dev.docx.gov.mn/soap/api"
        headers = {'Content-type': 'text/xml'}
        result = requests.post(target_url, data=data.encode(
            encoding='utf-8'), headers=headers, verify=False)

        if result.status_code == 200:

            mytree = ET.fromstring(result.content)

            status = mytree.find(
                './/{https://dev.docx.gov.mn/document/dto}responseCode')
            find = mytree.find(
                './/{https://dev.docx.gov.mn/document/dto}responseMessage')
            data = find.text.strip()
            if(status.text.strip() == '200'):
                return {'status': 200}
            else:
                return {'status': status.text.strip(), 'data': data}
        else:
            return {'status': 'ERROR', 'data': 'Сүлжээний алдаа гарлаа.'}
