# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2005-2006 Axelor SARL. (http://www.axelor.com)

import logging
import math

from collections import namedtuple

from datetime import datetime, date, timedelta, time
from pytz import timezone, UTC

from odoo import api, fields, models, SUPERUSER_ID, tools
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _
from odoo.osv import expression

_logger = logging.getLogger(__name__)

# Used to agglomerate the attendances in order to find the hour_from and hour_to
# See _onchange_request_parameters

class AttendanceRequest(models.Model):
    """ Leave Requests Access specifications

     - a regular employee / user
      - can see all leaves;
      - cannot see name field of leaves belonging to other user as it may contain
        private information that we don't want to share to other people than
        HR people;
      - can modify only its own not validated leaves (except writing on state to
        bypass approval);
      - can discuss on its leave requests;
      - can reset only its own leaves;
      - cannot validate any leaves;
     - an Officer
      - can see all leaves;
      - can validate "HR" single validation leaves from people if
       - he is the employee manager;
       - he is the department manager;
       - he is member of the same department;
       - target employee has no manager and no department manager;
      - can validate "Manager" single validation leaves from people if
       - he is the employee manager;
       - he is the department manager;
       - target employee has no manager and no department manager;
      - can first validate "Both" double validation leaves from people like "HR"
        single validation, moving the leaves to validate1 state;
      - cannot validate its own leaves;
      - can reset only its own leaves;
      - can refuse all leaves;
     - a Manager
      - can do everything he wants

    On top of that multicompany rules apply based on company defined on the
    leave request leave type.
    """
    _name = "hr.attendance.request"
    _description = "Attendance request"
    _order = "start_datetime desc"

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env.user.employee_id

    # description
    name = fields.Char('Name', required=True)
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),  # YTI This state seems to be unused. To remove
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
        ], string='Status', copy=False, default='draft',
        help="The status is set to 'To Submit', when a time off request is created." +
        "\nThe status is 'To Approve', when time off request is confirmed by user." +
        "\nThe status is 'Refused', when time off request is refused by manager." +
        "\nThe status is 'Approved', when time off request is approved by manager.")
    user_id = fields.Many2one('res.users', string='User')
    manager_id = fields.Many2one('hr.employee')
    request_status_type = fields.Selection([
        ('overtime', 'Overtime'),
        ('outside_work', 'Outside Work')
        ], string="Request Status Type")
    validation_type = fields.Selection([
        ('both', 'Both'),
        ('manager', 'Manager')
        ], string="Validation Type")
    employee_id = fields.Many2one(
        'hr.employee', string='Employee')
    notes = fields.Text('Reasons')
    # duration
    start_datetime = fields.Datetime(
        'Start Date', copy=False, required=True,
        default=fields.Datetime.now)
    end_datetime = fields.Datetime(
        'End Date', copy=False, required=True,
        default=fields.Datetime.now)
    request_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag')],
        string='Allocation Mode', required=True, default='employee')
    category_id = fields.Many2one(
        'hr.employee.category', string='Employee Tag')
    mode_company_id = fields.Many2one(
        'res.company', string='Company')
    department_id = fields.Many2one(
        'hr.department', string='Department')
    first_approver_id = fields.Many2one(
        'hr.employee', string='First Approval', copy=False)
    second_approver_id = fields.Many2one(
        'hr.employee', string='Second Approval', copy=False)
    

   