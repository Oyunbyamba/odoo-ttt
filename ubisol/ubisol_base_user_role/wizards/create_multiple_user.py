# -*- coding: utf-8 -*-
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class CreateMultipleUser(models.TransientModel):
    _name = 'create.multiple.user'
    _description = 'Хэрэглэгч олноор үүсгэх'

    department_ids = fields.Many2many('hr.department', string="Хэлтэс", help="Хэлтэс")
    
    def create_users(self):
        vals = []
        if self.department_ids:
            for department_id in self.department_ids:
                if department_id.member_ids:
                    for employee in department_id.member_ids:
                        if not employee.user_id.id and employee.work_email:
                            before_user = {
                                'login': employee.work_email, 
                                'password': employee.pin, 
                                'name': employee.name,
                                'email': employee.work_email
                                }
                            user = self.env['res.users'].create(before_user) 
                            employee.write({'user_id': user.id}) 
        return {}