# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from datetime import date, datetime, timedelta, time

_logger = logging.getLogger(__name__)

class HrEmployeeDirection(models.Model):
    _name = 'hr.employee.direction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'hr_employee_direction'

    def _get_default_user(self):
        return self.env.user

    name = fields.Char('Толгой')
    description = fields.Text('Их бие')
    direction_date = fields.Date('Тушаалын огноо', default=datetime.now().strftime('%Y-%m-%d'))
    direction_number = fields.Integer('Тушаалын дугаар')
    direction_attachment_ids = fields.Many2many(
        'ir.attachment', 'direction_doc_attach', 'direction_id', 'doc_id', string="Хавсралт", copy=False)
    state = fields.Selection([
        ('draft', 'Ноорог'),
        ('operate', 'Боловсруулсан'),
        ('confirm', 'Хянасан'),
        ('validate1', 'Зөвшөөрсөн'),
        ('validate', 'Баталсан')], default='draft',
        string='Төлөв', tracking=True)
    document_type_id = fields.Many2one('document.type', string='Тушаалын төрөл')    
    employee_ids = fields.Many2many('hr.employee', 'direction_hr_employee_rel', 'direction_id', 'emp_id', string='Ажилтан')
    user_id = fields.Many2one('res.users', string='Ноорог', default=_get_default_user)
    operate_user_id = fields.Many2one('res.users', string='Боловсруулсан')
    validate1_user_id = fields.Many2one('res.users', string='Хянасан')
    validate_user_id = fields.Many2one('res.users', string='Зөвшөөрсөн')
    confirm_user_id = fields.Many2one('res.users', string='Баталсан')


    def action_draft(self):
        self.write({'state': 'draft'})
        if any(holiday.state not in ['confirm', 'refuse'] for holiday in self):
            raise UserError(_('Time off request state must be "Refused" or "To Approve" in order to be reset to draft.'))
        self.write({
            'state': 'draft',
            'first_approver_id': False,
            'second_approver_id': False,
        })
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_draft()
            linked_requests.unlink()
        self.activity_update()
        return True

    def action_operate(self):
        self.write({'state': 'operate'})

    def action_validate1(self):
        if any(direction.state != 'operate' for direction in self):
            raise UserError(_('Direction must be confirmed ("To Operate") in order to approve it.'))
        self.write({'state': 'validate1'})

        # Post a second message, more verbose than the tracking message
        for direction in self.filtered(lambda direction: direction.validate1_user_id):
            direction.message_post(
                body=_('Your %s planned on %s has been accepted' % (direction.document_type_id.name, direction.direction_date)),
                partner_ids=direction.validate1_user_id.partner_id.ids)

    def action_validate(self):
        self.write({'state': 'validate'})    

    def action_confirm(self):
        self.write({'state': 'confirm'})
