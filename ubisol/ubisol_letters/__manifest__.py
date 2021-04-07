# -*- coding: utf-8 -*-
{
    'name': 'ubisol_letter',
    'version': '13.0.1.0.0',
    'category': 'Tools',
    'author': 'Odoo Mates',
    'website': "https://www.odoomates.com",
    'license': 'AGPL-3',
    'summary': 'Ubisol Letter',
    'description': 'turshilt',
    'depends': ['ubisol_hr_employee_upgrade', 'web_notify'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/mail_data.xml',
        'views/outgoing.xml',
        'views/incoming.xml',
        'views/planning.xml',
        'views/settings.xml',
        'views/res_partner.xml',
        'views/menu.xml',
        'wizards/letter_return_wizard.xml',
        'report/letter_detail.xml',
        'report/report.xml',


    ],
    'demo': [],
    'qweb': [
        'static/src/xml/import_letter.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
