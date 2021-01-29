# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'ubisol_hr_recruitment',
    'version': '1.0',
    'category': 'Uncategorized',
    'sequence': 90,
    'summary': 'Track your recruitment pipeline',
    'description': "",
    'website': 'https://www.odoo.com/page/recruitment',
    'depends': [
        'hr_recruitment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ubisol_hr_recruitment_security.xml',
        'views/hr_recruitment_views.xml',
        'views/hr_job_views.xml',
    ],
}
