# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)

# Inherit in your custom class


class UbisolLetters(http.Controller):

    @http.route('/docs/new_letter', auth='public', cors='*', csrf=False)
    def new_letter(self, **rec):
        if(rec.get('doc_id') and rec.get('org_id')):
            letter = request.env['ubi.letter.coming'].sudo().search([])
            new_letters = letter.check_new_letters()
            args = {'success': True}

        return "{'success': True}"

    @http.route('/docs/sent_letter_received', auth='public', cors='*', csrf=False)
    def receive_letter(self, **rec):
        if(rec.get('doc_id') and rec.get('org_id')):
            letter = request.env['ubi.letter.going'].sudo().search(
                [('tabs_id', '=', rec.get('doc_id'))])
            if letter:
                letter.state = 'received'

        return "{'success': True}"
    # api/docs/sentNotify?doc_id={docId}&org_id={org_id}&status={status}&info={info}

    @http.route('/docs/received_letter_returned', auth='public', cors='*', csrf=False)
    def return_letter(self, **rec):
        if(rec.get('doc_id') and rec.get('org_id')):
            letter = request.env['ubi.letter.coming'].sudo().search(
                [('tabs_id', '=', rec.get('doc_id'))])
            if letter:
                letter.state = 'refuse'

        return "{'success': True}"

    @http.route('/docs/incoming_graph', auth='user', type='json')
    def return_letter(self, **rec):

        total_incoming_month = request.env['ubi.letter.coming'].search_count([('create_date', '>=', datetime.now().strftime('%Y-%m-01')),
                ('create_date', '<', (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-01'))])
        total_incoming_day = request.env['ubi.letter.coming'].search_count([('create_date', '=', datetime.now().strftime('%Y-%m-%d'))])

        total_sending_month = request.env['ubi.letter.going'].search_count([('state', '=', 'sent'), 
                ('sent_date', '>=', datetime.now().strftime('%Y-%m-01')),
                ('sent_date', '<', (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-01'))])
        total_sending_day = request.env['ubi.letter.going'].search_count([('state', '=', 'sent'), 
                ('sent_date', '=', datetime.now().strftime('%Y-%m-%d'))])

        return {'html': request.env.ref('ubisol_letters.docs_incoming_dashboard_panel').render({
            'total_incoming_day': total_incoming_day,
            'total_incoming_month': total_incoming_month,
            'total_sending_day': total_sending_day,
            'total_sending_month': total_sending_month
        })
        }
