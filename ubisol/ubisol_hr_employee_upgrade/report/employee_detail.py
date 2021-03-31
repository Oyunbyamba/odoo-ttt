import logging
from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta, time


_logger = logging.getLogger(__name__)


class EmployeeDetailPdf(models.AbstractModel):
    _name = 'report.ubisol_hr_employee_upgrade.employee_detail_report'
    _description = 'Employee Anket Report'


    @api.model
    def _get_report_values(self, docids, data=None):
        _logger.info('_get_report_values')
        resume_lines = []
        employees = self.env['hr.employee'].browse(docids)
        for employee in employees:
            
            resume_lines = self.env['hr.resume.line'].search(
                [('employee_id', 'in', docids)])
            employee_skills = self.env['hr.employee.skill'].search(
                [('employee_id', 'in', docids)])
            employee_skills_internet = self.env['hr.employee.skill'].search(
                [('employee_id', 'in', docids), ('skill_type_id.name', '=', 'Интернетийн-орчинд-ажиллах')])
            employee_badges = self.env['gamification.badge.user'].search(
                [('employee_id', 'in', docids)])
            now_date = (datetime.now()).strftime('%Y-%m-%d')
            mergeshil = self.env['hr.resume.line'].search(
                [('employee_id', 'in', docids), ('line_type_id.name', '=', 'Мэргэшил')])
            if employee.birthday == False:
                birthday_year = ' '
                birthday_month = ' '
                birthday_day = ' '
            else:
                birthday_year = employee.birthday.strftime('%Y')
                birthday_month = employee.birthday.strftime('%m')
                birthday_day = employee.birthday.strftime('%d')
                
                
            language_skills = []
            speak = ''
            read = ''
            write = ''
            listen = ''
            obj = {}
            for employee_skill in employee_skills:

                language = False
                if employee_skill.skill_id.name == 'english':
                    language = True
                    name = employee_skill.skill_id.name
                    if employee_skill.skill_type_id.name == 'Ярих':
                        speak = employee_skill.skill_level_id.name
                    elif employee_skill.skill_type_id.name == 'Унших':
                        read = employee_skill.skill_level_id.name
                    elif employee_skill.skill_type_id.name == 'Бичих':
                        write = employee_skill.skill_level_id.name
                    elif employee_skill.skill_type_id.name == 'Сонсож-ойлгох':
                        listen = employee_skill.skill_level_id.name

                    if language:
                        obj = {
                            'name': name,
                            'listen': listen,
                            'speak': speak,
                            'read': read,
                            'write': write,
                        }
                        if name:
                            if listen:
                                if speak:
                                    if read:
                                        if write:
                                            language_skills.append(obj)
            speak = ''
            read = ''
            write = ''
            listen = ''
            for employee_skill in employee_skills:
                if employee_skill.skill_id.name == 'spain':
                    language = True
                    name = employee_skill.skill_id.name
                    if employee_skill.skill_type_id.name == 'Ярих':
                        speak = employee_skill.skill_level_id.name
                    elif employee_skill.skill_type_id.name == 'Унших':
                        read = employee_skill.skill_level_id.name
                    elif employee_skill.skill_type_id.name == 'Бичих':
                        write = employee_skill.skill_level_id.name
                    elif employee_skill.skill_type_id.name == 'Сонсож-ойлгох':
                        listen = employee_skill.skill_level_id.name

                    if language:
                        obj = {
                            'name': name,
                            'listen': listen,
                            'speak': speak,
                            'read': read,
                            'write': write,
                        }
                        if name:
                            if listen:
                                if speak:
                                    if read:
                                        if write:
                                            language_skills.append(obj)
            
            if mergeshil.date_end == False:
                delta1 = ' '
            else:    
                delta = mergeshil.date_end - mergeshil.date_start
                delta1 = delta.days
            return {
                'doc_model': 'hr.employee',
                'docs': employee,
                'resume_lines': resume_lines,
                'employee_badges': employee_badges,
                'employee_skills': employee_skills,
                'employee_skills_internet': employee_skills_internet,
                'now_date': now_date,
                'delta': delta1,
                'birthday_year': birthday_year,
                'birthday_month': birthday_month,
                'birthday_day': birthday_day,
                'language_skills': language_skills,
            }
        
