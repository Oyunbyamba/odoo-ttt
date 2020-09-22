# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from odoo import api, fields, models


class UbisolHolidaysRequest(models.Model): 
    _inherit = 'hr.leave'
    _description = "Time Off"

    years_of_worked_state = fields.Integer(
        'Улсад ажилласан жил', compute='_compute_years_of_worked_state', readonly=True)
    years_of_worked_company = fields.Integer(
        'Улсад ажилласан жил', compute='_compute_years_of_worked_company', readonly=True)
    employee_holiday = fields.Integer(
        'Улсад ажилласан жил', compute='_compute_employee_holiday', readonly=True)
   
    @api.depends('number_of_days')
    def _compute_number_of_days_display(self):
        for holiday in self:
            holiday.number_of_days_display = holiday.number_of_days  
            if(holiday.number_of_days <= 3 and holiday.holiday_status_id.validation_type == 'both'):
                if(holiday.holiday_status_id.unpaid == True):
                    holiday.holiday_status_id = 7
                else:
                    holiday.holiday_status_id = 9
            elif(holiday.number_of_days > 3 and holiday.holiday_status_id.validation_type != 'both'):
                if(holiday.holiday_status_id.unpaid == True):
                    holiday.holiday_status_id = 8
                else:
                    holiday.holiday_status_id = 10
    
   
    @api.onchange('holiday_status_id')
    def _compute_years_of_worked_state(self):
        for holiday in self:
            if(holiday.holiday_status_id.id == 11):
                holiday.years_of_worked_state = holiday.employee_id.years_of_civil_service

    @api.onchange('holiday_status_id')
    def _compute_years_of_worked_company(self):
        for holiday in self:
            if(holiday.holiday_status_id.id == 11):
                today = fields.Date.context_today(self)
                days = (today - holiday.employee_id.contract_signed_date).days
                holiday.years_of_worked_company = days
                
    @api.onchange('holiday_status_id')
    def _compute_employee_holiday(self):
        for holiday in self:
            if(holiday.holiday_status_id.id == 11):   
                if(holiday.employee_id.years_of_civil_service >= 6 and holiday.employee_id.years_of_civil_service <= 10):
                    holiday.employee_holiday = 18
                elif(holiday.employee_id.years_of_civil_service >= 11 and holiday.employee_id.years_of_civil_service <= 15):
                    holiday.employee_holiday = 20
                elif(holiday.employee_id.years_of_civil_service >= 16 and holiday.employee_id.years_of_civil_service <= 20):
                    holiday.employee_holiday = 22                 
                elif(holiday.employee_id.years_of_civil_service >= 21 and holiday.employee_id.years_of_civil_service <= 25):
                    holiday.employee_holiday = 24
                elif(holiday.employee_id.years_of_civil_service >= 26 and holiday.employee_id.years_of_civil_service <= 31):
                    holiday.employee_holiday = 26        
                elif(holiday.employee_id.years_of_civil_service >= 32):
                    holiday.employee_holiday = 29    