# -*- coding: utf-8 -*-
# from odoo import http


# class UbisolHrAttendanceUpgrade(http.Controller):
#     @http.route('/ubisol_hr_attendance_upgrade/ubisol_hr_attendance_upgrade/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ubisol_hr_attendance_upgrade/ubisol_hr_attendance_upgrade/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ubisol_hr_attendance_upgrade.listing', {
#             'root': '/ubisol_hr_attendance_upgrade/ubisol_hr_attendance_upgrade',
#             'objects': http.request.env['ubisol_hr_attendance_upgrade.ubisol_hr_attendance_upgrade'].search([]),
#         })

#     @http.route('/ubisol_hr_attendance_upgrade/ubisol_hr_attendance_upgrade/objects/<model("ubisol_hr_attendance_upgrade.ubisol_hr_attendance_upgrade"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ubisol_hr_attendance_upgrade.object', {
#             'object': obj
#         })
