# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)

# Inherit in your custom class
class UbisolLetters(http.Controller):

    @http.route('/docs/new_letter', auth='public', cors='*', csrf=False)
    def new_letter(self, **rec):
        _logger.info('new_letter')
        _logger.info(rec)
        if(rec['doc_id'] and rec['org_id']):
            letter = request.env['ubi.letter.coming'].sudo().search([])
            new_letters = letter.check_new_letters()
            _logger.info(new_letters)
            args = {'success': True}           
            
        return "{'success': True}"            

    @http.route('/docs/sent_letter_received', auth='public', cors='*', csrf=False)
    def receive_letter(self, **rec):
        _logger.info('sent_letter_received')
        _logger.info(rec)
        if(rec['doc_id'] and rec['org_id']):
            letter = request.env['ubi.letter.going'].sudo().search([('tabs_id', '=', rec['doc_id'])])          
            if letter:
                letter.state = 'received'

        return "{'success': True}"     


    @http.route('/docs/received_letter_returned', auth='public', cors='*', csrf=False)
    def return_letter(self, **rec):
        _logger.info('received_letter_returned')
        _logger.info(rec)
        if(rec['doc_id'] and rec['org_id']):
            letter = request.env['ubi.letter.coming'].sudo().search([('tabs_id', '=', rec['doc_id'])])          
            if letter:
                letter.state = 'refuse'

        return "{'success': True}"     