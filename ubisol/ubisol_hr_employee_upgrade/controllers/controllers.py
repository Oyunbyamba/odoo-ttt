# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class UbisolHrEmployeeUpgrade(http.Controller):
    # @http.route('/ubisol_hr_employee_upgrade/ubisol_hr_employee_upgrade/', auth='public')
    # def index(self, **kw):
    #     return "Hello, world"

    # @http.route('/ubisol_hr_employee_upgrade/ubisol_hr_employee_upgrade/objects/', auth='public')
    # def list(self, **kw):
    #     return http.request.render('ubisol_hr_employee_upgrade.listing', {
    #         'root': '/ubisol_hr_employee_upgrade/ubisol_hr_employee_upgrade',
    #         'objects': http.request.env['ubisol_hr_employee_upgrade.ubisol_hr_employee_upgrade'].search([]),
    #     })

    # @http.route('/ubisol_hr_employee_upgrade/ubisol_hr_employee_upgrade/objects/<model("ubisol_hr_employee_upgrade.ubisol_hr_employee_upgrade"):obj>/', auth='public')
    # def object(self, obj, **kw):
    #     return http.request.render('ubisol_hr_employee_upgrade.object', {
    #         'object': obj
    #     })

    @http.route('/ubisol_hr_employee_upgrade/get_lat_long', type='json', auth='user')
    def check_employee_location(self, **rec):
        latitude = 0
        longitude = 0
        if request.jsonrequest:
            if(rec['uid']):
                employee = request.env['hr.employee'].sudo().search([('user_id', '=', rec['uid'])])
                if employee:
                    latitude = employee.latitude
                    longitude = employee.longitude
        args = {'success': True, 'latitude': latitude, 'longitude': longitude}           
        return args    

    # @http.route('/ubisol_hr_employee_upgrade/set_my_lat_long', type='json', auth='user')
    # def set_my_lat_long(self, **rec):
    #     if request.jsonrequest:
    #         if(rec['uid']):
    #             employee = request.env['hr.employee'].sudo().search([('user_id', '=', rec['uid'])])
    #             if employee:
    #                 latitude = employee.latitude
    #                 longitude = employee.longitude
    #                 print(longitude)
    #                 print(latitude)
    #     args = {'success': True, 'latitude': latitude, 'longitude': longitude}           
    #     return args         
