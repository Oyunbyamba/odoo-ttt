# -*- coding: utf-8 -*-
# from odoo import http


# class UbisolHrAttendanceReport(http.Controller):
#     @http.route('/ubisol_hr_attendance_report/ubisol_hr_attendance_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ubisol_hr_attendance_report/ubisol_hr_attendance_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ubisol_hr_attendance_report.listing', {
#             'root': '/ubisol_hr_attendance_report/ubisol_hr_attendance_report',
#             'objects': http.request.env['ubisol_hr_attendance_report.ubisol_hr_attendance_report'].search([]),
#         })

#     @http.route('/ubisol_hr_attendance_report/ubisol_hr_attendance_report/objects/<model("ubisol_hr_attendance_report.ubisol_hr_attendance_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ubisol_hr_attendance_report.object', {
#             'object': obj
#         })
