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
        _logger.info('new_letter')
        if(rec.get('doc_id') and rec.get('org_id')):
            _logger.info(rec.get('org_id'))
            letter = request.env['ubi.letter.coming'].sudo().search([])
            new_letters = letter.check_new_letters()
            _logger.info(new_letters)
            args = {'success': True}

        return "{'success': True}"

    @http.route('/docs/sent_letter_received', auth='public', cors='*', csrf=False)
    def receive_letter(self, **rec):
        _logger.info('sent_letter_received')
        _logger.info(rec)
        if(rec.get('doc_id') and rec.get('org_id')):
            letter = request.env['ubi.letter.going'].sudo().search(
                [('tabs_id', '=', rec.get('doc_id'))])
            if letter:
                letter.state = 'received'

        return "{'success': True}"
    # api/docs/sentNotify?doc_id={docId}&org_id={org_id}&status={status}&info={info}

    @http.route('/docs/received_letter_returned', auth='public', cors='*', csrf=False)
    def return_letter(self, **rec):
        _logger.info('received_letter_returned')
        _logger.info(rec)
        if(rec.get('doc_id') and rec.get('org_id')):
            letter = request.env['ubi.letter.coming'].sudo().search(
                [('tabs_id', '=', rec.get('doc_id'))])
            if letter:
                letter.state = 'refuse'

        return "{'success': True}"

    @http.route('/docs/incoming_graph', auth='user', type='json')
    def return_letter(self, **rec):

        # total_incoming_month = request.env['ubi.letter.coming'].search_count([('create_date', '&lt;', (datetime.now()
        #                                                                                               + relativedelta(day=1)).strftime('%%Y-%%m-%%d')), ('create_date', '&gt;=', datetime.now().strftime('%%Y-%%m-%%d'))])
        # total_incoming_day = request.env['ubi.letter.coming'].search_count([('create_date', '&lt;', (
        #    datetime.now() + relativedelta(months=1)).strftime('%%Y-%%m-01')), ('create_date', '&gt;=', datetime.now().strftime('%%Y-%%m-01'))])
        return {'html': request.env.ref('ubisol_letters.docs_incoming_dashboard_panel').render({
            'total_incoming_day': 20,  # total_incoming_day,
            'total_incoming_month': 30,  # total_incoming_month,
            'total_sending_day': 25,
            'total_sending_month': 26
        })
        }
