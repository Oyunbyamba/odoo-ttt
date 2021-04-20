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
from odoo.exceptions import ValidationError, AccessError, UserError

_logger = logging.getLogger(__name__)


class UbiLetterComing(models.Model):
    _name = "ubi.letter.coming"
    _inherit = ['ubi.letter', 'mail.thread', 'mail.activity.mixin']
    _description = " Ирсэн бичиг"
    _rec_name = 'letter_number'
    _mail_post_access = 'read'

    follow_id = fields.Many2one('ubi.letter.going', groups="base.group_user")
    letter_attachment_ids = fields.Many2many(
        'ir.attachment', 'letter_coming_doc_attach', 'letter_id', 'doc_id', string="Хавсралт", copy=False)
    state = fields.Selection([
        ('conflict', 'Зөрчилтэй'),
        ('draft', 'Ирсэн'),
        ('receive', 'Хүлээн авсан'),
        ('refuse', 'Буцаасан'),
        ('review', 'Судлаж байгаа'),
        ('transfer', 'Шилжүүлсэн'),
        ('validate', 'Шийдвэрлэсэн')],
        groups="base.group_user",
        default='draft',
        string='Ирсэн бичгийн төлөв', store=True, readonly=True, copy=False, tracking=True)
    going_letters = fields.Many2one(
        'ubi.letter.going', string='Явсан бичгийн дугаар', groups="base.group_user")
    cancel_employee = fields.Char(
        string="Цуцалсан ажилтан", groups="base.group_user", help="Ажилтан")
    cancel_position = fields.Char(
        string='Цуцалсан ажилтны ажил', groups="base.group_user")
    cancel_comment = fields.Char(
        string='Цуцалсан утга', groups="base.group_user")
    # can_approve = fields.Boolean('Can reset', compute='_compute_can_approve', groups="base.group_user")

    def call_return_wizard(self):
        if len(self.ids) >= 1:
            if any(letter.state not in ['receive', 'review', 'transfer'] or letter.is_local not in [False] for letter in self):
                raise UserError(
                    _('Хүлээн авсан, судлаж байгаа, шилжүүлсэн төлөвтэй баримтыг "Буцаасан" төлөвт оруулах боломжтой.'))

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

    # @api.onchange('letter_template_id')
    # def _set_letter_template(self):
    #     if self.letter_template_text:
    #         self.custom_letter_template = self.letter_template_text

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

    @api.onchange('department_id')
    def _manager_department_id(self):
        if self.department_id:
            self.user_id = self.department_id.manager_id.user_id if self.department_id.manager_id else ''

    @api.model
    def create(self, vals):
        letter = super(UbiLetterComing, self).create(vals)
        if not letter.tabs_id:
            letter.state = 'receive'
            letter.receive_user_id = self.env.user

        return letter

    def write(self, vals):
        letter = super(UbiLetterComing, self).write(vals)

        return letter

    # ------------------------------------------------------------
    # Activity methods
    # ------------------------------------------------------------

    # def _get_responsible_for_approval(self):
    #     self.ensure_one()
    #     responsible = self.env['res.users'].browse(SUPERUSER_ID)

    #     if self.validation_type == 'manager' or (self.validation_type == 'both' and self.state == 'confirm'):
    #         if self.employee_id.leave_manager_id:
    #             responsible = self.employee_id.leave_manager_id
    #         elif self.employee_id.parent_id.user_id:
    #             responsible = self.employee_id.parent_id.user_id
    #     elif self.validation_type == 'hr' or (self.validation_type == 'both' and self.state == 'validate1'):
    #         if self.holiday_status_id.responsible_id:
    #             responsible = self.holiday_status_id.responsible_id

    #     return responsible

    def action_review(self):
        if any(letter.state not in ['receive'] for letter in self):
            raise UserError(
                _('Зөвхөн хүлээн авсан төлөвтэй баримтыг "Судлаж байгаа" төлөвт оруулах боломжтой.'))
        self.write({'state': 'review'})
        return True

    def action_transfer(self):
        if any(letter.state not in ['review'] for letter in self):
            raise UserError(
                _('Зөвхөн судлаж байгаа төлөвтэй баримтыг "Шилжүүлсэн" төлөвт оруулах боломжтой.'))
        self.write({'state': 'transfer'})
        self.user_id.notify_info(message='Таньд 1 шинэ бичиг шилжиж ирлээ.')
        self.activity_update()
        return True

    def action_validate(self):
        if any(letter.state not in ['transfer', 'review', 'receive'] for letter in self):
            raise UserError(
                _('Зөвхөн хүлээн авсан, шилжүүлсэн төлөвтэй баримтыг "Зөвшөөрсөн" төлөвт оруулах боломжтой.'))
        self.write({'state': 'validate'})
        return True

    # def _compute_can_approve(self):

    @api.model
    def check_new_letters(self, user={}):
        data = """<Envelope xmlns = "http://schemas.xmlsoap.org/soap/envelope/" >
                    <Body>
                        <callRequest xmlns = "https://docx.gov.mn/document/dto">
                            <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                            <service>get.document_list/list</service >
                            <params>{}</params>

                        </callRequest>
                    </Body>
                </Envelope>"""

        # result = client.service.call(data)
        # print(result)

        target_url = "https://docx.gov.mn/soap/api"
        headers = {'Content-type': 'text/xml'}
        result = requests.post(target_url, data=data.encode(
            encoding='utf-8'), headers=headers, verify=False)

        if result.status_code == 200:

            mytree = ET.fromstring(result.content)

            status = mytree.find(
                './/{https://docx.gov.mn/document/dto}responseCode')

            if(status.text.strip() == '200'):
                find = mytree.find(
                    './/{https://docx.gov.mn/document/dto}data')

                data = json.loads(find.text.strip())
                count = 0
                for doc in data:
                    already_received = self.env['ubi.letter.coming'].search(
                        [('tabs_id', '=', doc['id']), ('partner_id.ubi_letter_org_id', '=', doc['orgId'])], limit=1)
                    # umnu orj irseng shalgah
                    if(already_received):
                        pass
                    else:
                        vals = self.prepare_receiving(doc)
                        self.env['ubi.letter.coming'].create(vals)
                        count += 1
                return 'Шинээр нийт ' + str(count) + ' бичиг ирсэн байна.'

            else:
                return 'Албан бичиг татах системтэй холбогдох явцад алдаа гарлаа.'
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
        vals['draft_user_id'] = self.env.user.id
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
        vals['state'] = 'draft'
        vals['is_local'] = False

        return vals

    def download_files(self, files):
        attachment_ids = []
        for file in files:
            file_url = "https://docx.gov.mn"+file['url']
            file_name = file['name']
            result = base64.b64encode(requests.get(
                file_url.strip(), verify=False).content).replace(b'\n', b'')
            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': result,
                'res_model': 'ubi.letter.coming'
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
        letters = self.env['ubi.letter.coming'].browse(ids)
        for letter in letters:
            if letter.state == 'receive':
                params = {"id": letter.tabs_id, "cancelPerson": wizard_vals.cancel_employee.name, "cancelPosition": wizard_vals.cancel_position,
                          "cancelComment": wizard_vals.cancel_comment}
                result = self.return_received(params)
                if result['status'] == '200':
                    letter.write({"state": "refuse",
                                  "cancel_comment": wizard_vals.cancel_comment,
                                  "cancel_position": wizard_vals.cancel_position,
                                  "cancel_employee": wizard_vals.cancel_employee.name
                                  })
                else:
                    raise UserError(_(result['data']))
        return True

    def return_received(self, params):

        template = """<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                        <Body>
                            <callRequest xmlns="https://docx.gov.mn/document/dto">
                                <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                                <service>post.public.document/receive</service>
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
                './/{https://docx.gov.mn/document/dto}responseCode')
            find = mytree.find(
                './/{https://docx.gov.mn/document/dto}data')
            msg = mytree.find(
                './/{https://docx.gov.mn/document/dto}responseMessage')
            _logger.info(data)

            if(status.text.strip() == '200'):
                return {'status': status.text.strip(), 'data': []}
            else:
                return {'status': status.text.strip(), 'data': msg.text.strip()}
        else:
            return {'status': 'ERROR', 'data': 'Сүлжээний алдаа гарлаа.'}

    def letter_receiving(self):
        if any(letter.state not in ['draft'] for letter in self):
            raise UserError(
                _('Зөвхөн ирсэн төлөвтэй баримтыг "Хүлээн авсан" төлөвт оруулах боломжтой.'))

        letters = self.env['ubi.letter.coming'].browse(self.ids)
        for letter in letters:
            if letter.state == 'draft':
                received_user = self.env.user
                params = {"id": letter.tabs_id,
                          "statusId": 6,
                          "statusPerson": received_user.employee_id.name if received_user.employee_id else "",
                          "statusPosition": received_user.employee_id.job_id.name if received_user.employee_id else "",
                          "statusComment": ""}
                result = self.letter_received(params)
                if result['status'] == '200':
                    letter.write(
                        {"state": "receive", 'receive_user_id': received_user})
                else:
                    raise UserError(_(result['data']))
        return True

    def letter_received(self, params):

        template = """<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                        <Body>
                            <callRequest xmlns="https://docx.gov.mn/document/dto">
                                <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                                    <service>post.public.document/receive</service>
                                <params>%s</params>
                            </callRequest>
                        </Body>
                    </Envelope>"""
        data = template % params
        _logger.info(data)
        target_url = "https://docx.gov.mn/soap/api"
        headers = {'Content-type': 'text/xml'}
        result = requests.post(target_url, data=data.encode(
            encoding='utf-8'), headers=headers, verify=False)

        if result.status_code == 200:
            mytree = ET.fromstring(result.content)

            status = mytree.find(
                './/{https://docx.gov.mn/document/dto}responseCode')
            find = mytree.find(
                './/{https://docx.gov.mn/document/dto}data')
            msg = mytree.find(
                './/{https://docx.gov.mn/document/dto}responseMessage')

            if(status.text.strip() == '200'):
                data = json.loads(find.text.strip())
                return {'status': status.text.strip(), 'data': data}
            else:
                return {'status': status.text.strip(), 'data': msg.text.strip()}
        else:
            return {'status': 'ERROR', 'data': 'Сүлжээний алдаа гарлаа.'}

    def activity_update(self):
        to_clean, to_do = self.env['ubi.letter.going'], self.env['ubi.letter.going']
        for letter in self:
            note = _('%s дугаартай баримтыг %s -нд %s -с шилжүүлсэн.') % (letter.letter_number,
                                                                          fields.Datetime.to_string(letter.processing_datetime), self.env.user.name)
            # if letter.state == 'draft':
            #     to_clean |= holiday
            if letter.state == 'transfer':
                letter.activity_schedule(
                    'ubisol_letters.mail_act_letter_coming_transfer',
                    note=note,
                    user_id=letter.user_id.id or self.env.user.id)
            # elif letter.state == 'validate1':
            #     letter.activity_feedback(['ubisol_letters.mail_act_leave_approval'])
            #     letter.activity_schedule(
            #         'ubisol_letters.mail_act_leave_second_approval',
            #         note=note,
            #         user_id=letter.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif letter.state == 'validate':
                to_do |= letter
            # elif letter.state == 'refuse':
            #     to_clean |= letter
        # if to_clean:
        #     to_clean.activity_unlink(['ubisol_letters.mail_act_leave_approval', 'ubisol_letters.mail_act_leave_second_approval'])
        if to_do:
            to_do.activity_feedback(
                ['ubisol_letters.mail_act_letter_coming_transfer'])

    ####################################################
    # Messaging methods
    ####################################################

    def _track_subtype(self, init_values):
        if 'state' in init_values and self.state == 'transfer':
            return self.env.ref('ubisol_letters.mt_transferred')
        return super(UbiLetterComing, self)._track_subtype(init_values)
