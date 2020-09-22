# -*- coding: utf-8 -*-
# from odoo import http


# class UbisolHrHolidays(http.Controller):
#     @http.route('/ubisol_hr_holidays/ubisol_hr_holidays/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ubisol_hr_holidays/ubisol_hr_holidays/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ubisol_hr_holidays.listing', {
#             'root': '/ubisol_hr_holidays/ubisol_hr_holidays',
#             'objects': http.request.env['ubisol_hr_holidays.ubisol_hr_holidays'].search([]),
#         })

#     @http.route('/ubisol_hr_holidays/ubisol_hr_holidays/objects/<model("ubisol_hr_holidays.ubisol_hr_holidays"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ubisol_hr_holidays.object', {
#             'object': obj
#         })
