# -*- coding: utf-8 -*-
# from odoo import http


# class UbisolLoginTemplate(http.Controller):
#     @http.route('/ubisol_login_template/ubisol_login_template/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ubisol_login_template/ubisol_login_template/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ubisol_login_template.listing', {
#             'root': '/ubisol_login_template/ubisol_login_template',
#             'objects': http.request.env['ubisol_login_template.ubisol_login_template'].search([]),
#         })

#     @http.route('/ubisol_login_template/ubisol_login_template/objects/<model("ubisol_login_template.ubisol_login_template"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ubisol_login_template.object', {
#             'object': obj
#         })
