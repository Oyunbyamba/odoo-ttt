# -*- coding: utf-8 -*-
{
    'name': 'Ubisol Letter',
    'version': '13.0.1.0.0',
    'category': 'Tools',
    'author': 'Odoo Mates',
    'website': "https://www.odoomates.com",
    'license': 'AGPL-3',
    'summary': 'Ubisol Letter',
    'description': 'turshilt',
    'depends': ['ubisol_hr_employee_upgrade'],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/views.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
