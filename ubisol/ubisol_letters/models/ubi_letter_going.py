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
    _description = " Албан бичиг"
    _rec_name = 'letter_number'
    _mail_post_access = 'read'

    follow_id = fields.Many2one('ubi.letter.coming', groups="base.group_user")
    letter_attachment_ids = fields.Many2many(
        'ir.attachment', 'letter_going_doc_attach', 'letter_id', 'doc_id', string="Хавсралт", copy=False)
    state = fields.Selection([
        ('draft', 'Бүртгэсэн'),
        ('confirm', 'Хянасан'),
        ('validate1', 'Зөвшөөрсөн'),
        ('expected', 'Хүлээгдэж буй'),
        ('sent', 'Илгээсэн'),
        ('refuse', 'Буцаасан'),
        ('receive', 'Хүлээн авсан'),
        ('validate', 'Баталсан')
        ],
        groups="base.group_user",
        default='draft',
        string='Явсан бичгийн төлөв', store=True, readonly=True, copy=False, tracking=True)
    send_date = fields.Date(
        string='Илгээсэн огноо', groups="base.group_user")
    coming_letter = fields.Many2one(
        'ubi.letter.coming', string='Ирсэн бичгийн хариу', groups="base.group_user")
    letter_template_id = fields.Many2one(
        'ubi.letter.template', string='Баримтын загвар', groups="base.group_user")
    letter_template_text = fields.Html(
        'Агуулга', groups="base.group_user")
    custom_letter_template = fields.Html('Template', groups="base.group_user")
    paper_size = fields.Selection(
        'Paper size', related="letter_template_id.paper_size")
    next_step_user = fields.Many2one('res.users', compute='_compute_next_step_user')
    can_approve = fields.Boolean('Can Approve', compute='_compute_can_approve')


    def _set_custom_template(self):
        if self.custom_letter_template:
            self.custom_letter_template = self.custom_letter_template

    def replace_template_text(self, key_word, val):
        template_text = self.custom_letter_template
        soup = BeautifulSoup(template_text, 'html.parser')
        match = soup.find('span', {'id': key_word})
        match.string = val
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

    @api.onchange('coming_letter')
    def _computed_letter_type(self):
        self.computed_letter_type = ''
        if self.coming_letter:
            self.computed_letter_type = self.coming_letter.letter_type_id.name if self.coming_letter.letter_type_id else ''

    @api.onchange('coming_letter')
    def _computed_letter_subject(self):
        self.computed_letter_subject = ''
        if self.coming_letter:
            self.computed_letter_subject = self.coming_letter.letter_subject_id.name if self.coming_letter.letter_subject_id else ''

    @api.onchange('coming_letter')
    def _computed_letter_desc(self):
        self.computed_letter_desc = ''
        if self.coming_letter:
            self.computed_letter_desc = self.coming_letter.desc

    @api.onchange('confirm_user_id', 'validate1_user_id', 'validate_user_id')
    def _compute_next_step_user(self):
        if self.state == 'draft' and self.confirm_user_id:
            self.next_step_user = self.confirm_user_id
        elif self.state == 'confirm' and self.validate1_user_id:
            self.next_step_user = self.validate1_user_id
        elif self.state == 'validate1' and self.validate_user_id:
            self.next_step_user = self.validate_user_id            

    @api.model
    def create(self, vals):
        letter = super(UbiLetterGoing, self).create(vals)
        if vals.get('confirm_user_id'):
            self.next_step_user.notify_info(message='Таньд 1 тушаал шилжиж ирлээ.')
            self.activity_update()

        if letter.request_employee_id:
            self.add_follower(letter.request_employee_id)
        if letter.responsible_employee_id:
            self.add_follower(letter.responsible_employee_id)

        return letter

    def write(self, vals):
        letter = super(UbiLetterGoing, self).write(vals)
        if vals.get('confirm_user_id') or vals.get('validate1_user_id') or (vals.get('validate_user_id') and self.state != 'expected'):
            self.next_step_user.notify_info(message='Таньд 1 тушаал шилжиж ирлээ.')
            self.activity_update()
            
        if self.request_employee_id:
            self.add_follower(self.request_employee_id)
        if self.responsible_employee_id:
            self.add_follower(self.responsible_employee_id)

        return letter

    def _compute_can_approve(self):
        current_user = self.env.user
        is_officer = self.env.user.has_group('hr.group_hr_user')
        is_manager = self.env.user.has_group('hr.group_hr_manager')
        can_approve = False
        if not is_manager:
            if self.state == 'draft' and current_user == self.confirm_user_id:
                can_approve = True
            elif self.state == 'confirm' and current_user == self.validate1_user_id:
                can_approve = True
            elif self.state == 'validate1' and current_user == self.validate_user_id:
                can_approve = True
        else:
            can_approve = True        
        self.can_approve = can_approve

    def print_report(self):
        if self.letter_template_id:
            if self.letter_template_id.paper_size == 'a4':
                report = self.env.ref('ubisol_letters.letter_detail_report_a4_pdf')
            elif self.letter_template_id.paper_size == 'a5':
                report = self.env.ref('ubisol_letters.letter_detail_report_a5_pdf')
            
            return report.report_action(self.ids)

    def prepare_sending(self):
        letters = self.env['ubi.letter.going'].browse(self.ids)
        for letter in letters:
            if any(letter.state not in ['expected'] for letter in self):
                raise UserError(
                    _('Зөвхөн хүлээгдэж буй төлөвтэй баримтыг "Илгээх" төлөвт оруулах боломжтой.'))

            if letter.is_local == True:
                raise UserError(    
                    _('Зөвхөн гадаад баримтыг "ТАБС-р" илгээх боломжтой.'))

            if letter.state == 'expected':
                request_data = self.build_state_doc(letter)
                result = self.send_letter(request_data)
                if result['status'] == '200':
                    data = result['data']
                    letter.write(
                        {"state": "sent", "tabs_id": data['id'], "send_date": datetime.today().strftime('%Y-%m-%d'), "user_id": self.env.user.id})
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
        body['isReplyDoc'] = True if letter.coming_letter else False
        body['isNeedReply'] = letter.must_return
        # datetime.strftime(letter.letter_date, '%Y-%m-%d') if letter.letter_date else ''
        body['priorityId'] = letter.priority_id
        body['noOfPages'] = letter.letter_total_num
        body['responseTypeID'] = 1  # letter.must_return  # nuhtsul shalgah
        # mistyped asuuh heregtei
        body['responseDate'] = datetime.strftime(
            letter.must_return_date, '%Y-%m-%d') if letter.must_return_date else ''
        # 1 #letter.coming_letter.letter_number or ''
        body['srcDocumentNumber'] = letter.coming_letter.letter_number if letter.coming_letter else ''
        # body['srcDocumentCode'] = letter.coming_letter.tabs_id if letter.coming_letter else ''
        body['srcDocumentDate'] = datetime.strftime(
            letter.coming_letter.letter_date, '%Y-%m-%d') if letter.coming_letter and letter.coming_letter.letter_date else ''

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


    # ------------------------------------------------------------
    # Activity methods
    # ------------------------------------------------------------

    def action_sent(self):
        if any(letter.state not in ['expected'] for letter in self):
            raise UserError(_('Зөвхөн хүлээгдэж буй бичгийг "Илгээх" төлөвт оруулах боломжтой.'))
        self.write({'state': 'sent', "send_date": datetime.today().strftime('%Y-%m-%d'), "user_id": self.env.user.id})

        for letter in self:
            before_letter_vals = letter.copy_data({
                'letter_date': datetime.today().strftime('%Y-%m-%d'),
                'state': 'draft',
                'follow_id': letter.id,
                'desc': letter.letter_template_text
            })[0]
            del before_letter_vals['send_date']
            del before_letter_vals['coming_letter']
            del before_letter_vals['letter_template_id']
            del before_letter_vals['letter_template_text']
            del before_letter_vals['custom_letter_template']

            incoming_letter = self.env['ubi.letter.coming'].search([('follow_id', '=', letter.id)])
            if incoming_letter:
                incoming_letter.write(before_letter_vals)
            else:
                coming_letter = self.env['ubi.letter.coming'].with_context(local_transfer=True).create(before_letter_vals)

        return True

    def action_refuse(self):
        if any(letter.state in ['receive'] for letter in self):
            raise UserError(_('Хүлээн авсан бичгийг "Буцаах" төлөвт оруулах боломжгүй байна.'))
        self.write({'state': 'refuse'})
        incoming_letter = self.env['ubi.letter.coming'].search([('follow_id', '=', self.id)])
        if incoming_letter:
            incoming_letter.write({'state': 'refuse'})
            user_name = self.env.user.employee_id.name if self.env.user.employee_id else self.env.user.name     
            note = _("%s дугаартай албан бичгийг 'Буцаасан' төлөвт '%s' орууллаа.") % (incoming_letter.letter_number, user_name)    
            incoming_letter.message_post(body=note)

        return True

    def action_draft(self):
        if any(letter.state not in ['confirm', 'validate1', 'validate'] for letter in self):
            raise UserError(_('"Ноорог" төлөвт оруулах боломжгүй байна.'))
        self.write({
            'state': 'draft',
            'confirm_user_id': False,
            'validate1_user_id': False,
            'validate_user_id': False
        })
        return True

    def action_confirm(self):
        if self.filtered(lambda letter: letter.state != 'draft'):
            raise UserError(_('Зөвхөн ноорог төлөвтэй албан бичгийг "Боловсруулсан" төлөвт оруулах боломжтой.'))
        self.write({'state': 'confirm'})

        self.activity_feedback(['ubisol_letters.mail_act_letter_confirm'])
        return True

    def action_validate1(self):
        if any(letter.state != 'confirm' for letter in self):
            raise UserError(_('Зөвхөн боловсруулсан төлөвтэй албан бичгийг "Зөвшөөрсөн" төлөвт оруулах боломжтой.'))
        self.write({'state': 'validate1'})

        self.activity_feedback(['ubisol_letters.mail_act_letter_validate1'])

        return True

    def action_validate(self):
        if any(letter.state not in ['validate1'] for letter in self):
            raise UserError(_('Зөвхөн зөвшөөрсөн төлөвтэй албан бичгийг "Баталсан" төлөвт оруулах боломжтой.'))
        
        self.write({'state': 'validate'})
        self.activity_feedback(['ubisol_letters.mail_act_letter_validate'])  
        return True

    def action_expected(self):
        if any(letter.state not in ['validate','refuse'] for letter in self):
            raise UserError(_('Зөвхөн баталсан төлөвтэй албан бичгийг "Хүлээгдэж буй" төлөвт оруулах боломжтой.'))
        
        self.write({'state': 'expected'})
        self.activity_feedback(['ubisol_letters.mail_act_letter_expected'])  
        return True


    def activity_update(self):
        to_clean, to_do = self.env['ubi.letter.going'], self.env['ubi.letter.going']
        
        for letter in self:
            if letter.state == 'draft':
                next_state = 'Хянасан'
                format_name = 'ubisol_letters.mail_act_letter_confirm'
                to_do |= letter
            elif letter.state == 'confirm':
                next_state = 'Зөвшөөрсөн'
                format_name = 'ubisol_letters.mail_act_letter_validate1'
                to_do |= letter
            elif letter.state == 'validate1':
                next_state = 'Баталсан'
                format_name = 'ubisol_letters.mail_act_letter_validate'
                to_do |= letter

            user_name = self.next_step_user.employee_id.name if self.next_step_user.employee_id else self.next_step_user.name
            note = _("%s дугаартай албан бичиг %s -р '%s' төлөвт шилжүүлэгдэхээр хүлээгдэж байна.") % (letter.letter_number, user_name, next_state)    
            letter.activity_schedule(
                format_name,
                note=note,
                user_id=self.next_step_user.id or self.env.user.id)

        return True

    ####################################################
    # Messaging methods
    ####################################################

    def _track_subtype(self, init_values):
        if 'state' in init_values and self.state == 'transfer':
            return self.env.ref('ubisol_letters.mt_transferred')
        return super(UbiLetterGoing, self)._track_subtype(init_values)

    def add_follower(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id.id)
        if employee.user_id:
            self.message_subscribe(partner_ids=employee.user_id.partner_id.ids)

    def message_subscribe(self, partner_ids=None, channel_ids=None, subtype_ids=None):
        # due to record rule can not allow to add follower and mention on validated leave so subscribe through sudo
        if self.state in ['validate', 'validate1']:
            self.check_access_rights('read')
            self.check_access_rule('read')
            return super(UbiLetterGoing, self.sudo()).message_subscribe(partner_ids=partner_ids, channel_ids=channel_ids, subtype_ids=subtype_ids)
        return super(UbiLetterGoing, self).message_subscribe(partner_ids=partner_ids, channel_ids=channel_ids, subtype_ids=subtype_ids)
            