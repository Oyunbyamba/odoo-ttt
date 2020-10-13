# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Attendance request',
    'version': '1.5',
    'category': 'Human Resources/Time Off',
    'summary': 'Overtime, out of office requests',
    'description': """
Manage overtime requests and out of office
=====================================

This application controls the overtime schedule of your company. It allows employees to request overtime. Then, managers can review requests for overtime and approve or reject them. This way you can control the overall overtime planning for the company or department.

""",
    'depends': ['hr', 'calendar', 'resource', 'ubisol_hr_employee_upgrade'],
    'data': [
        'security/ir.model.access.csv',

        'views/attendance_request_views.xml',
        'views/hr_views.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
