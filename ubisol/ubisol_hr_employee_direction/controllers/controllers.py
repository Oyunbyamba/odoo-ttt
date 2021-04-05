# -*- coding: utf-8 -*-
# from odoo import http


# class UbisolDirection(http.Controller):
#     @http.route('/ubisol_direction/ubisol_direction/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ubisol_direction/ubisol_direction/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ubisol_direction.listing', {
#             'root': '/ubisol_direction/ubisol_direction',
#             'objects': http.request.env['ubisol_direction.ubisol_direction'].search([]),
#         })

#     @http.route('/ubisol_direction/ubisol_direction/objects/<model("ubisol_direction.ubisol_direction"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ubisol_direction.object', {
#             'object': obj
#         })
