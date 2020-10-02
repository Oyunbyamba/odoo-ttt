# -*- coding: utf-8 -*-
import base64
import json
from odoo import http, fields
from odoo.http import request
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.modules.module import get_module_resource


class UbisolHrEmployeeUpgrade(http.Controller):
   
    # @http.route('/ubisol_hr_employee_upgrade/ubisol_hr_employee_upgrade/objects/', auth='public')
    # def list(self, **kw):
    #     return http.request.render('ubisol_hr_employee_upgrade.listing', {
    #         'root': '/ubisol_hr_employee_upgrade/ubisol_hr_employee_upgrade',
    #         'objects': http.request.env['ubisol_hr_employee_upgrade.ubisol_hr_employee_upgrade'].search([]),
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

    @http.route('/ubisol_hr_employee_upgrade/set_my_lat_long', type='json', auth='user')
    def set_my_lat_long(self, **rec):
        # print(rec)
        now = fields.Datetime.now()
        today = fields.Date.today()
        create_date = False
        if request.jsonrequest:
            if(rec['uid'] and rec['state'] and rec['file']):
                image_str = rec["file"]
                employee = request.env['hr.employee'].sudo().search([('user_id', '=', rec['uid'])])
                if employee:
                    last_attendance_before_check_in = request.env['hr.attendance'].search([
                            ('employee_id', '=', employee.id),
                            ('check_in', '<', now),
                        ], order='check_in desc', limit=1)
                    print(last_attendance_before_check_in)
                    last_picture_before_check_in = request.env['hr.employee.picture'].search([
                                ('employee_id', '=', employee.id),
                                ('check_in', '<', now),
                            ], order='check_in desc', limit=1)

                    if(last_attendance_before_check_in): 
                        create_date = last_attendance_before_check_in.create_date.date()    
                    
                    if(rec['state'] == 'check_in'):
                        if(create_date == False or (create_date and create_date < today)):
                            vals = {
                                'employee_id': employee.id,
                                'check_in': now,
                            }
                            request.env['hr.attendance'].create(vals)

                            vals = {
                                'employee_id': employee.id,
                                'name': image_str,
                                'check_in': now,
                            }
                            request.env['hr.employee.picture'].create(vals)
                    elif(rec['state'] == 'check_out'):
                        if(create_date and create_date == today):
                            last_attendance_before_check_in.check_out = now
                            last_picture_before_check_in.check_out = now
                            last_picture_before_check_in.second_pic = image_str
                        
            args = {'success': True}           
            return args         