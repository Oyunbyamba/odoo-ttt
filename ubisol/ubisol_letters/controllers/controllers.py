# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


# Inherit in your custom class
class LetterBanner(http.Controller):

    @http.route('/ubisol_letters/letter_banner', auth='user', type='json')
    def letter_banner(self):
        return {
            'html': """
                    <link href="/ubisol_letters/static/src/css/banner.css" rel="stylesheet">  
                      """
        }
