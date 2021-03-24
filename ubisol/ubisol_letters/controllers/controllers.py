# -*- coding: utf-8 -*-
# from odoo import http


# class UbisolBaseMenu(http.Controller):
#     @http.route('/ubisol_base_menu/ubisol_base_menu/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ubisol_base_menu/ubisol_base_menu/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ubisol_base_menu.listing', {
#             'root': '/ubisol_base_menu/ubisol_base_menu',
#             'objects': http.request.env['ubisol_base_menu.ubisol_base_menu'].search([]),
#         })

#     @http.route('/ubisol_base_menu/ubisol_base_menu/objects/<model("ubisol_base_menu.ubisol_base_menu"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ubisol_base_menu.object', {
#             'object': obj
#         })
