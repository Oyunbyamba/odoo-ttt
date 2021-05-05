# -*- coding: utf-8 -*-
import logging
import requests
import json
import base64
import xml.etree.ElementTree as ET
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, AccessError, UserError

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    @api.model
    def default_get(self, fields):
        res = super(ResPartner, self).default_get(fields)
        if (not fields or 'ubi_letter_org' in fields) and 'ubi_letter_org' in res:
            res['is_company'] = True
        return res

    ubi_letter_org = fields.Boolean(string='Харилцагч байгууллага мөн эсэх', default=False)
    ubi_letter_org_id = fields.Integer(string='Харилцагч байгууллагын код')

    @api.model
    def create(self, vals):
        if vals.get('name'):
            prev_company = self.env['res.partner'].search([('ubi_letter_org', '=', True), ('name', '=', vals.get('name'))])
            if prev_company:
                raise UserError(_('Харилцагч байгууллагын нэр давхардсан байна.'))

        if vals.get('ubi_letter_org_id'):
            prev_company = self.env['res.partner'].search([('ubi_letter_org', '=', True), ('ubi_letter_org_id', '=', vals.get('ubi_letter_org_id'))])
            if prev_company:
                raise UserError(_('Харилцагч байгууллагын код давхардсан байна.'))   

        res_partner = super(ResPartner, self).create(vals)

        return res_partner    

    # def change_field_values(self):


    def search_organization(self):
        if (self.name != '' or self.name != False):
            template = """<Envelope xmlns = "http://schemas.xmlsoap.org/soap/envelope/" >
                                <Body>
                                    <callRequest xmlns = "https://dev.docx.gov.mn/document/dto">
                                        <token>2mRCiuLX352m6O2lhqMoxPs-fQ5ibZgaqIHRbNSaxCaoiJg7Ugo7nCCQEMKKlgK-XBQBprEqylE3EKmM5fMinLm6PnzAYfIHTi-BcwQXG8l3MHKp30HFjMyfrhfJvqK83o4JhtDxAXyp8TpeRrEhY949ClikAWr-v1cPbQ6Q0N8</token>
                                        <service>get.org/list</service >
                                        <params>%s</params>
                                    </callRequest>
                                </Body>
                            </Envelope>"""

            params = {"name": self.name}                
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
                    './/{https://dev.docx.gov.mn/document/dto}data')
                msg = mytree.find(
                    './/{https://dev.docx.gov.mn/document/dto}responseMessage')

                data = json.loads(find.text.strip())

                if(status.text.strip() == '200'):
                    if data[0]['name']:
                        self.env['organization.list.wizard'].search([]).unlink()
                        org_obj = self.env['organization.list.wizard'].create(
                            {'organization_name': data[0]['name'], 'organization_code': data[0]['id']})

                        return {
                            'name': _('Үр дүн'),
                            'type': 'ir.actions.act_window',
                            'view_mode': 'tree',
                            'res_model': 'organization.list.wizard',
                            'target': 'new',
                            'active_id': self.id
                        }    

            else:
                return {'status': 'ERROR', 'data': 'Сүлжээний алдаа гарлаа.'}
        