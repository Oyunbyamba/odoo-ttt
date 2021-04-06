# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from datetime import date, datetime, timedelta, time
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class HrEmployeeDirection(models.Model):
    _name = 'hr.employee.direction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'hr_employee_direction'

    def _get_default_user(self):
        return self.env.user

    def _compute_can_approve(self):
        # if self.env.is_superuser():
        #     return
        # current_employee = self.env.user.employee_id

        current_user = self.env.user
        is_officer = self.env.user.has_group('hr.group_hr_user')
        is_manager = self.env.user.has_group('hr.group_hr_manager')
        can_approve = False
        if not is_manager:
            if self.state == 'draft' and current_user == self.operate_user_id:
                can_approve = True
            elif self.state == 'operate' and current_user == self.confirm_user_id:
                can_approve = True
            elif self.state == 'confirm' and current_user == self.validate1_user_id:
                can_approve = True
            elif self.state == 'validate1' and current_user == self.validate_user_id:
                can_approve = True
        else:
            can_approve = True        
        self.can_approve = can_approve

    name = fields.Char('Толгой', readonly=True, states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    description = fields.Text('Их бие', readonly=True, states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    direction_date = fields.Date('Тушаалын огноо', default=datetime.now().strftime('%Y-%m-%d'), readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    direction_number = fields.Integer('Тушаалын дугаар', readonly=True, states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    direction_attachment_ids = fields.Many2many(
        'ir.attachment', 'direction_doc_attach', 'direction_id', 'doc_id', string="Хавсралт", readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]}, copy=False)
    state = fields.Selection([
        ('draft', 'Илгээх'),
        ('refuse', 'Татгалзсан'),
        ('operate', 'Боловсруулсан'),
        ('confirm', 'Хянасан'),
        ('validate1', 'Зөвшөөрсөн'),
        ('validate', 'Баталсан')], default='draft', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]},
        string='Төлөв', tracking=True)
    document_type_id = fields.Many2one('document.type', string='Тушаалын төрөл', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]}, groups="hr.group_hr_user")    
    # employee_ids = fields.Many2many('hr.employee', 'direction_hr_employee_rel', 'direction_id', 'emp_id', 
    #     string='Ажилтан', readonly=True, required=True,
    #     states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})

    employee_id = fields.Many2one('hr.employee', 
        string='Ажилтан', readonly=True, required=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})    
    user_id = fields.Many2one('res.users', string='Ноорог', default=_get_default_user)
    operate_user_id = fields.Many2one('res.users', string='Боловсруулах', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    confirm_user_id = fields.Many2one('res.users', string='Хянах', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    validate1_user_id = fields.Many2one('res.users', string='Зөвшөөрөх', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    validate_user_id = fields.Many2one('res.users', string='Батлах', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    can_approve = fields.Boolean('Can Approve', compute='_compute_can_approve')

    def action_draft(self):
        if any(direction.state not in ['refuse'] for direction in self):
            raise UserError(_('Direction state must be "To Approve" in order to be reset to draft.'))
        self.write({
            'state': 'draft',
            'operate_user_id': False,
            'validate1_user_id': False,
            'validate_user_id': False,
            'confirm_user_id': False,
        })
        # self.activity_update()
        return True

    def action_operate(self):
        if self.filtered(lambda direction: direction.state != 'draft'):
            raise UserError(_('Time off request must be in Draft state ("To Operate") in order to confirm it.'))
        self.write({'state': 'operate'})

        return True

    def action_confirm(self):
        if self.filtered(lambda direction: direction.state != 'operate'):
            raise UserError(_('Time off request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm'})

        #     # Automatic validation should be done in sudo, because user might not have the rights to do it by himself
        #     holidays.sudo().action_validate()

        # self.activity_update()
        return True

    def action_validate1(self):
        if any(direction.state != 'confirm' for direction in self):
            raise UserError(_('Direction must be confirmed ("To Approve") in order to approve it.'))
        self.write({'state': 'validate1'})

        # Post a second message, more verbose than the tracking message
        for direction in self.filtered(lambda direction: direction.validate1_user_id):
            direction.message_post(
                body=_('Your %s planned on %s has been accepted' % (direction.document_type_id.name, direction.direction_date)),
                partner_ids=direction.validate1_user_id.partner_id.ids)

        return True

    def action_validate(self):
        current_employee = self.env.user.employee_id
        if any(direction.state not in ['confirm', 'validate1'] for direction in self):
            raise UserError(_('Time off request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})
        # self.filtered(lambda holiday: holiday.validation_type == 'both').write({'second_approver_id': current_employee.id})
        # self.filtered(lambda holiday: holiday.validation_type != 'both').write({'first_approver_id': current_employee.id})
    
        return True

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(direction.state not in ['operate', 'confirm', 'validate', 'validate1'] for direction in self):
            raise UserError(_('Direction must be confirmed or validated in order to refuse it.'))

        self.write({'state': 'refuse'})
        # validated_holidays = self.filtered(lambda hol: hol.state == 'validate1')
        # validated_holidays.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        # (self - validated_holidays).write({'state': 'refuse', 'second_approver_id': current_employee.id})
    
        return True


                            