# -*- coding: utf-8 -*-
# from odoo import http


# class UbisolHrEmployeeShift(http.Controller):
#     @http.route('/ubisol_hr_employee_shift/ubisol_hr_employee_shift/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ubisol_hr_employee_shift/ubisol_hr_employee_shift/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ubisol_hr_employee_shift.listing', {
#             'root': '/ubisol_hr_employee_shift/ubisol_hr_employee_shift',
#             'objects': http.request.env['ubisol_hr_employee_shift.ubisol_hr_employee_shift'].search([]),
#         })

#     @http.route('/ubisol_hr_employee_shift/ubisol_hr_employee_shift/objects/<model("ubisol_hr_employee_shift.ubisol_hr_employee_shift"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ubisol_hr_employee_shift.object', {
#             'object': obj
#         })
