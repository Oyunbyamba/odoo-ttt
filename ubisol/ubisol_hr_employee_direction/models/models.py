# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from datetime import date, datetime, timedelta, time
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class HrEmployeeDirection(models.Model):
    _name = 'hr.employee.direction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Тушаал'

    def _get_default_user(self):
        return self.env.user

    def _user_id_domain(self):
        if self.user_has_groups('hr.group_hr_manager'):
            return []
        return [('user_id', '=', self.env.user.id)]     

    def _operate_user_id_domain(self):
        # if self.user_has_groups('hr_contract.group_hr_contract_manager') or self.user_has_groups('hr_holidays.group_hr_holidays_manager'):
        if self.user_has_groups('hr.group_hr_manager'):
            return []
        # if self.user_has_groups('hr_holidays.group_hr_holidays_responsible'):
        #     return [('leave_manager_id', '=', self.env.user.id)]
        return [('operate_user_id', '=', self.env.user.id)] 

    def _confirm_user_id_domain(self):
        if self.user_has_groups('hr.group_hr_manager'):
            return []
        return [('confirm_user_id', '=', self.env.user.id)]                           

    def _validate1_user_id_domain(self):
        if self.user_has_groups('hr.group_hr_manager'):
            return []
        return [('validate1_user_id', '=', self.env.user.id)]   

    def _validate_user_id_domain(self):
        if self.user_has_groups('hr.group_hr_manager'):
            return []
        return [('validate_user_id', '=', self.env.user.id)]                

    name = fields.Char('Толгой', readonly=True, states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    description = fields.Html('Их бие', readonly=True, states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    direction_date = fields.Date('Тушаалын огноо', default=datetime.now().strftime('%Y-%m-%d'), readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    direction_number = fields.Char('Тушаалын дугаар', readonly=True, states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    direction_attachment_ids = fields.Many2many(
        'ir.attachment', 'direction_doc_attach', 'direction_id', 'doc_id', string="Хавсралт", readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]}, copy=False)
    state = fields.Selection([
        ('draft', 'Ноорог'),
        ('refuse', 'Татгалзсан'),
        ('operate', 'Боловсруулсан'),
        ('confirm', 'Хянасан'),
        ('validate1', 'Зөвшөөрсөн'),
        ('validate', 'Баталсан')], default='draft', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]},
        string='Төлөв', tracking=True)
    hr_document_id = fields.Many2one('hr.document', string='Тушаалын загвар', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]}, groups="hr.group_hr_user")    
    # employee_ids = fields.Many2many('hr.employee', 'direction_hr_employee_rel', 'direction_id', 'emp_id', 
    #     string='Ажилтан', readonly=True, required=True,
    #     states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})
    
    employee_id = fields.Many2one('hr.employee', 
        string='Ажилтан', readonly=True, required=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]})    
    user_id = fields.Many2one('res.users', string='Ноорог', default=_get_default_user, domain=_user_id_domain)
    operate_user_id = fields.Many2one('res.users', string='Боловсруулах', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]},
        domain=_operate_user_id_domain)
    confirm_user_id = fields.Many2one('res.users', string='Хянах', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]},
        domain=_confirm_user_id_domain)
    validate1_user_id = fields.Many2one('res.users', string='Зөвшөөрөх', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]},
        domain=_validate1_user_id_domain)
    validate_user_id = fields.Many2one('res.users', string='Батлах', readonly=True,
        states={'draft': [('readonly', False)], 'operate': [('readonly', False)]},
        domain=_validate_user_id_domain)
    can_approve = fields.Boolean('Can Approve', compute='_compute_can_approve')
    next_step_user = fields.Many2one('res.users', compute='_compute_next_step_user')

    @api.onchange('hr_document_id')
    def _set_letter_template(self):
        self.description = self.hr_document_id.note
        
      
    @api.onchange('direction_date')
    def _set_letter_template1(self):
        if self.hr_document_id:
            string = self.description
            number = self.direction_date
            number_str = str(number)
            find0 = string.find("$dire_date")
            asd = str("-1")

            if (str(find0) != asd):
                print(str(find0))
                self.description = string.replace(
                    "$dire_date", number_str)
                string = self.description
            
            else:
                self.description = self.hr_document_id.note
                string = self.description
                self.description = string.replace(
                    "$dire_date", number_str)
                string = self.description
                if self.employee_id.name:
                    self.description = string.replace(
                        "$name", str(self.employee_id.name))
                    string = self.description
                if self.employee_id.identification_id:
                    self.description = string.replace(
                        "$register", str(self.employee_id.identification_id))
                    string = self.description
                if self.employee_id.job_title:
                    self.description = string.replace(
                        "$position", str(self.employee_id.job_title))
                    string = self.description
                if self.employee_id.surname:
                    self.description = string.replace(
                        "$ovog", str(self.employee_id.surname))
                    string = self.description
               

    @api.onchange('employee_id')
    def _set_letter_template2(self):
        if self.hr_document_id:
            string = self.description
            employee_id = self.employee_id.name
            employee_id_str = str(employee_id)
            find0 = string.find("$name")
            asd = str("-1")
            if (str(find0) != asd):
                self.description = string.replace(
                    "$name", employee_id_str)
                string = self.description
                self.description = string.replace(
                    "$dire_date", str(self.direction_date))
                string = self.description
            else:
                self.description = self.hr_document_id.note
                string = self.description
                self.description = string.replace(
                    "$name", str(self.employee_id.name))
                string = self.description
                if self.direction_date:
                    self.description = string.replace(
                        "$dire_date", str(self.direction_date))
                    string = self.description
                if self.employee_id.identification_id:
                    self.description = string.replace(
                        "$register", str(self.employee_id.identification_id))
                    string = self.description
                if self.employee_id.job_title:
                    self.description = string.replace(
                        "$position", str(self.employee_id.job_title))
                    string = self.description
                if self.employee_id.surname:
                    self.description = string.replace(
                        "$ovog", str(self.employee_id.surname))
                    string = self.description
        if self.hr_document_id:
            string = self.description
            draft_user_id_str = str(self.employee_id.identification_id)
            find0 = string.find("$register")
            asd = str("-1")
            if (str(find0) != asd):
                self.description = string.replace(
                    "$register", draft_user_id_str)
                string = self.description
                self.description = string.replace(
                    "$dire_date", str(self.direction_date))
                string = self.description
            else:
                self.description = self.hr_document_id.note
                string = self.description
                self.description = string.replace(
                    "$register", draft_user_id_str)
                string = self.description
                if self.direction_date:
                    self.description = string.replace(
                        "$dire_date", str(self.direction_date))
                    string = self.description
                if self.employee_id.name:
                    self.description = string.replace(
                        "$name", str(self.employee_id.name))
                    string = self.description
                if self.employee_id.job_title:
                    self.description = string.replace(
                        "$position", str(self.employee_id.job_title))
                    string = self.description
                if self.employee_id.surname:
                    self.description = string.replace(
                        "$ovog", str(self.employee_id.surname))
                    string = self.description

        if self.hr_document_id:
            string = self.description
            letter_subject_id = self.employee_id.job_title
            letter_subject_id_str = str(letter_subject_id)
            find0 = string.find("$position")
            asd = str("-1")
            if (str(find0) != asd):
                self.description = string.replace(
                    "$position", letter_subject_id_str)
                string = self.description
                self.description = string.replace(
                    "$dire_date", str(self.direction_date))
                string = self.description
            else:
                self.description = self.hr_document_id.note
                string = self.description
                self.description = string.replace(
                    "$position", letter_subject_id_str)
                string = self.description

                if self.direction_date:
                    self.description = string.replace(
                        "$dire_date", str(self.direction_date))
                    string = self.description
                if self.employee_id.name:
                    self.description = string.replace(
                        "$name", str(self.employee_id.name))
                    string = self.description
                if self.employee_id.identification_id:
                    self.description = string.replace(
                        "$register", str(self.employee_id.identification_id))
                    string = self.description
                if self.employee_id.surname:
                    self.description = string.replace(
                        "$ovog", str(self.employee_id.surname))
                    string = self.description
        if self.hr_document_id:
            string = self.description
            letter_total_num = self.employee_id.surname
            letter_total_num_str = str(letter_total_num)
            find0 = string.find("$ovog")
            asd = str("-1")
            if (str(find0) != asd):
                self.description = string.replace(
                    "$ovog", letter_total_num_str)
                string = self.description
                self.description = string.replace(
                    "$dire_date", str(self.direction_date))
                string = self.description
            else:
                self.description = self.hr_document_id.note
                string = self.description
                self.description = string.replace(
                    "$ovog", letter_total_num_str)
                string = self.description

                if self.direction_date:
                    self.description = string.replace(
                        "$dire_date", str(self.direction_date))
                    string = self.description
                if self.employee_id.name:
                    self.description = string.replace(
                        "$name", str(self.employee_id.name))
                    string = self.description
                if self.employee_id.identification_id:
                    self.description = string.replace(
                        "$register", str(self.employee_id.identification_id))
                    string = self.description
                if self.employee_id.job_title:
                    self.description = string.replace(
                        "$position", str(self.employee_id.job_title))
                    string = self.description
                        

    @api.onchange('operate_user_id', 'confirm_user_id', 'validate1_user_id', 'validate_user_id')
    def _compute_next_step_user(self):
        if self.state == 'draft' and self.operate_user_id:
            self.next_step_user = self.operate_user_id
        elif self.state == 'operate' and self.confirm_user_id:
            self.next_step_user = self.confirm_user_id
        elif self.state == 'confirm' and self.validate1_user_id:
            self.next_step_user = self.validate1_user_id
        elif self.state == 'validate1' and self.validate_user_id:
            self.next_step_user = self.validate_user_id            


    def _compute_can_approve(self):
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


    @api.model 
    def create(self, vals):
        direction = super(HrEmployeeDirection, self).create(vals)
        if vals.get('operate_user_id') or vals.get('confirm_user_id') or vals.get('validate1_user_id') or vals.get('validate_user_id'):
            direction.next_step_user.notify_info(message='Таньд 1 тушаал шилжиж ирлээ.')
            direction.activity_update()

        return direction

    def write(self, vals):
        direction = super(HrEmployeeDirection, self).write(vals)
        if vals.get('operate_user_id') or vals.get('confirm_user_id') or vals.get('validate1_user_id') or vals.get('validate_user_id'):
            self.next_step_user.notify_info(message='Таньд 1 тушаал шилжиж ирлээ.')
            self.activity_update()

        return direction

    # ------------------------------------------------------------
    # Activity methods
    # ------------------------------------------------------------

    def action_draft(self):
        if any(direction.state not in ['refuse'] for direction in self):
            raise UserError(_('Зөвхөн татгалзсан төлөвтэй тушаалыг "Ноорог" төлөвт оруулах боломжтой.'))
        self.write({
            'state': 'draft',
            'operate_user_id': False,
            'validate1_user_id': False,
            'validate_user_id': False,
            'confirm_user_id': False,
        })

        self.activity_feedback(['ubisol_hr_employee_direction.mail_act_direction_refuse'])
        # self.activity_update()
        return True

    def action_operate(self):
        if self.filtered(lambda direction: direction.state != 'draft'):
            raise UserError(_('Зөвхөн ноорог төлөвтэй тушаалыг "Боловсруулсан" төлөвт оруулах боломжтой.'))
        self.write({'state': 'operate'})

        self.activity_feedback(['ubisol_hr_employee_direction.mail_act_direction_processing'])
        return True

    def action_confirm(self):
        if self.filtered(lambda direction: direction.state != 'operate'):
            raise UserError(_('Зөвхөн боловсруулсан төлөвтэй тушаалыг "Хянасан" төлөвт оруулах боломжтой.'))
        self.write({'state': 'confirm'})

        self.activity_feedback(['ubisol_hr_employee_direction.mail_act_direction_confirm'])
        return True

    def action_validate1(self):
        if any(direction.state != 'confirm' for direction in self):
            raise UserError(_('Зөвхөн хянасан төлөвтэй тушаалыг "Зөвшөөрсөн" төлөвт оруулах боломжтой.'))
        self.write({'state': 'validate1'})
        self.activity_feedback(['ubisol_hr_employee_direction.mail_act_direction_validate1'])
        # Post a second message, more verbose than the tracking message
        # for direction in self.filtered(lambda direction: direction.validate1_user_id):
            # direction.message_post(
            #     body=_('Your %s planned on %s has been accepted' %
            #            (direction.hr_document_id.name, direction.direction_date)),
            #     partner_ids=direction.validate1_user_id.partner_id.ids)

        return True

    def action_validate(self):
        current_employee = self.env.user.employee_id
        if any(direction.state not in ['confirm', 'validate1'] for direction in self):
            raise UserError(_('Зөвхөн зөвшөөрсөн төлөвтэй тушаалыг "Баталсан" төлөвт оруулах боломжтой.'))
        
        self.write({'state': 'validate'})
        self.activity_feedback(['ubisol_hr_employee_direction.mail_act_direction_validate'])  
        return True

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(direction.state not in ['operate', 'confirm', 'validate', 'validate1'] for direction in self):
            raise UserError(_('Тушаалыг "Татгалзсан" төлөвт оруулах боломжгүй төлөвт байна.'))
        self.write({'state': 'refuse'})
        self.activity_update()
        self.user_id.notify_info(message=self.direction_number + ' дугаартай тушаалыг татгалзсан байна.')
        return True


    def activity_update(self):
        to_clean, to_do = self.env['hr.employee.direction'], self.env['hr.employee.direction']
        
        for direction in self:
            if direction.state == 'draft':
                next_state = 'Боловсруулсан'
                format_name = 'ubisol_hr_employee_direction.mail_act_direction_processing'
            elif direction.state == 'operate':
                next_state = 'Хянасан'
                format_name = 'ubisol_hr_employee_direction.mail_act_direction_confirm'
                to_do |= direction
            elif direction.state == 'confirm':
                next_state = 'Зөвшөөрсөн'
                format_name = 'ubisol_hr_employee_direction.mail_act_direction_validate1'
                to_do |= direction
            elif direction.state == 'validate1':
                next_state = 'Баталсан'
                format_name = 'ubisol_hr_employee_direction.mail_act_direction_validate'
                to_do |= direction
            elif direction.state == 'refuse':
                format_name = 'ubisol_hr_employee_direction.mail_act_direction_refuse'
                user_name = self.env.user.employee_id.name if self.env.user.employee_id else self.env.user.name
                note = _("%s дугаартай тушаалыг %s -с 'Татгалзсан' төлөвт оруулсан байна.") % (direction.direction_number, user_name)    
                direction.activity_schedule(
                    format_name,
                    note=note,
                    user_id=self.user_id.id or self.env.user.id)

                return True

            user_name = self.next_step_user.employee_id.name if self.next_step_user.employee_id else self.next_step_user.name
            note = _("%s дугаартай тушаал %s -р '%s' төлөвт шилжүүлэгдэхээр хүлээгдэж байна.") % (direction.direction_number, user_name, next_state)    
            direction.activity_schedule(
                format_name,
                note=note,
                user_id=self.next_step_user.id or self.env.user.id)

        # if to_clean:
        #     to_clean.activity_unlink(['ubisol_letters.mail_act_leave_approval', 'ubisol_letters.mail_act_leave_second_approval'])
        # if to_do:
        #     to_do.activity_feedback(['ubisol_hr_employee_direction.mail_act_direction_processing'])    
        return True

    ####################################################
    # Messaging methods
    ####################################################

    # def _track_subtype(self, init_values):
    #     if 'state' in init_values and self.state == 'transfer':
    #         return self.env.ref('ubisol_hr_employee_direction.mt_transferred')
    #     return super(HrEmployeeDirection, self)._track_subtype(init_values)    