# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from odoo import api, fields, _, models


class UbisolHolidaysRequest(models.Model): 
    _inherit = 'hr.leave'
    _description = "Time Off"

    years_of_worked_state = fields.Integer('Улсад ажилласан жил', compute='_compute_years_of_worked_state', readonly=True)
    years_of_worked_company = fields.Float('Байгууллагад ажилласан жил', digits=(2,1), compute='_compute_years_of_worked_company', readonly=True)
    employee_holiday = fields.Integer('Ажилласан жил', compute='_compute_employee_holiday', readonly=True)
    warning_of_vacation = fields.Char('Ээлжийн амралт боломжтой эсэх', compute='_compute_warning_of_vacation', readonly=True)    
    vacation_type = fields.Boolean('Ээлжийн амралт эсэх', compute='_compute_vacation_type', default=False)    
    company_holiday_days = fields.Integer('Суурь амралтын хоног', compute='_compute_company_holiday_days', default=15, readonly=True)
   
    def get_filtered_record(self):
        record_ids = []
        user = self.env['res.users'].browse(self._uid)
        employee_pool = self.env['hr.employee']
        employee = employee_pool.search([('user_id', '=', user.id)])
        if user.has_group('hr_holidays.group_hr_holidays_manager') | user.has_group('hr_holidays.group_hr_holidays_user'):
            record_ids = self.env['hr.leave'].search(['|', ('state', '=', "validate1"), ('employee_id.leave_manager_id', '=', user.id)]).ids
        elif user.has_group('hr_holidays.group_hr_holidays_responsible'):
            record_ids = self.env['hr.leave'].search([('employee_id.leave_manager_id', '=', user.id)]).ids
        return {
            'name': _('Leaves'),
            'domain': [('id', 'in', record_ids)],
            'res_model': 'hr.leave',
            'view_type': 'form',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }           

    @api.depends('number_of_days')
    def _compute_number_of_days_display(self):
        for holiday in self:
            holiday.number_of_days_display = holiday.number_of_days  
            if(holiday.number_of_days <= holiday.holiday_status_id.one_step_days and holiday.holiday_status_id.validation_type == 'both'):
                if(holiday.holiday_status_id.unpaid == True):
                    holiday.holiday_status_id = 6
                else:
                    holiday.holiday_status_id = 8
            elif(holiday.number_of_days > holiday.holiday_status_id.one_step_days and holiday.holiday_status_id.validation_type != 'both'):
                if(holiday.holiday_status_id.unpaid == True):
                    holiday.holiday_status_id = 7
                else:
                    holiday.holiday_status_id = 9  
                    
    @api.onchange('holiday_status_id')
    def _compute_company_holiday_days(self):
        for holiday in self:
            if(holiday.holiday_status_id.vacation == True):
                holiday.company_holiday_days = 15
                contract_date = holiday.employee_id.contract_signed_date
                if(contract_date):
                    today = fields.Date.today()
                    months = (today.year - contract_date.year)*12+today.month-contract_date.month
                    if(months < 11): 
                        holiday.company_holiday_days = round((months*15)/11)
   
    @api.onchange('holiday_status_id')
    def _compute_years_of_worked_state(self):
        for holiday in self:
            if(holiday.holiday_status_id.vacation == True):
                holiday.years_of_worked_state = holiday.employee_id.years_of_civil_service
            else:
                holiday.years_of_worked_state = 0

    @api.onchange('holiday_status_id')
    def _compute_years_of_worked_company(self):
        for holiday in self:
            if(holiday.holiday_status_id.vacation == True):
                contract_date = holiday.employee_id.contract_signed_date
                if(contract_date):
                    today = fields.Date.context_today(self)
                    months = (today.year - contract_date.year)*12+today.month-contract_date.month
                    if(months < 11): 
                        holiday.warning_of_vacation = 'Ажилласан сар 11-с бага байна.'
                    years = months/12
                    holiday.years_of_worked_company = years
            else:
                holiday.years_of_worked_company = 0
                holiday.warning_of_vacation = ''  
                
    @api.onchange('holiday_status_id')
    def _compute_employee_holiday(self):
        for holiday in self:
            if(holiday.holiday_status_id.vacation == True):
                if(holiday.employee_id.years_of_civil_service <= 5):  
                    holiday.employee_holiday = holiday.company_holiday_days
                elif(holiday.employee_id.years_of_civil_service >= 6 and holiday.employee_id.years_of_civil_service <= 10):
                    holiday.employee_holiday = holiday.company_holiday_days+3
                elif(holiday.employee_id.years_of_civil_service >= 11 and holiday.employee_id.years_of_civil_service <= 15):
                    holiday.employee_holiday = holiday.company_holiday_days+5
                elif(holiday.employee_id.years_of_civil_service >= 16 and holiday.employee_id.years_of_civil_service <= 20):
                    holiday.employee_holiday = holiday.company_holiday_days+7                 
                elif(holiday.employee_id.years_of_civil_service >= 21 and holiday.employee_id.years_of_civil_service <= 25):
                    holiday.employee_holiday = holiday.company_holiday_days+9
                elif(holiday.employee_id.years_of_civil_service >= 26 and holiday.employee_id.years_of_civil_service <= 31):
                    holiday.employee_holiday = holiday.company_holiday_days+11        
                elif(holiday.employee_id.years_of_civil_service >= 32):
                    holiday.employee_holiday = holiday.company_holiday_days+14    
            else:
                holiday.employee_holiday = 0        

    @api.onchange('holiday_status_id')
    def _compute_vacation_type(self):
        for holiday in self:
            if(holiday.holiday_status_id.vacation == True):
                holiday.vacation_type = True
            else: 
                holiday.vacation_type = False              

