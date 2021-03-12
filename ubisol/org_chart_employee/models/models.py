# -*- coding: utf-8 -*-
from odoo import models, fields, api
import base64
import tempfile


class OrgChartEmployee(models.Model):
    _name = 'org.chart.employee'

    name = fields.Char("Org Chart Employee")

    @api.model
    def get_employee_data(self):
        company = self.env.user.company_id
        data = {
            'name': company.name,
            'title': company.country_id.name,
            'children': [],
            'office': "<img src='/logo.png' />",
        }
        departments = self.env['hr.department'].search(
            [('parent_id', '=', False)])
        # employees = self.env['hr.employee'].search([('parent_id', '=', False)])
        # for employee in departments:
        #    data['children'].append(
        #        self.get_children(employee, 'middle-level'))

        for department in departments:
            data['children'].append(
                self.get_children_dep(department, 'middle-level'))

        return {'values': data}

    @api.model
    def get_children(self, emp, style=False):
        data = []
        emp_data = {'name': emp.name, 'title': self._get_position(
            emp), 'office': self._get_image(emp)}
        childrens = self.env['hr.employee'].search(
            [('parent_id', '=', emp.id)])
        for child in childrens:
            # self.env['hr.employee'].search([('parent_id','=',child.id)])
            sub_child = False
            next_style = self._get_style(style)
            if not sub_child:
                data.append({'name': child.name, 'title': self._get_position(
                    child), 'className': next_style, 'office': self._get_image(child)})
            else:
                data.append(self.get_children(child, next_style))

        if childrens:
            emp_data['children'] = data
        if style:
            emp_data['className'] = style

        return emp_data

    @api.model
    def get_children_dep(self, dep, style=False):
        data = []
        dep_data = {'name': self._get_fullname(dep), 'title': dep.name, 'total': self._get_dep_emp_count(dep),
                    'office': self._get_image(dep)}
        childrens = self.env['hr.department'].search(
            [('parent_id', '=', dep.id)])
        for child in childrens:
            # self.env['hr.employee'].search([('parent_id','=',child.id)])
            sub_child = False
            next_style = self._get_style(style)
            if not sub_child:
                data.append({'name': self._get_fullname(dep), 'title': dep.name, 'total': self._get_dep_emp_count(dep),
                             'className': next_style, 'office': self._get_image(dep)})
            else:
                data.append(self.get_children(child, next_style))

        if childrens:
            dep_data['children'] = data
        if style:
            dep_data['className'] = style

        return dep_data

    def _get_style(self, last_style):
        if last_style == 'middle-level':
            return 'product-dept'
        if last_style == 'product-dept':
            return 'rd-dept'
        if last_style == 'rd-dept':
            return 'pipeline1'
        if last_style == 'pipeline1':
            return 'frontend1'

        return 'middle-level'

    def _get_image(self, dep):
        if dep.manager_id.image_128:
            image_path = "/web/image/hr.employee/%s/image_1920" % (
                dep.manager_id)
            return '<img src=%s />' % (image_path)

        image_path = "/org_chart_employee/static/src/img/default_image.png"
        return '<img src=%s />' % (image_path)

    def _get_position(self, dep):
        if dep.manager_id.sudo().job_id:
            return dep.manager_id.sudo().job_id.name
        return ""

    def _get_fullname(self, dep):
        if dep.manager_id.surname:
            return dep.manager_id.surname[0] + '.' + dep.manager_id.name
        elif dep.manager_id:
            return '.' + dep.manager_id.name
        else:
            return ''

    def _get_dep_emp_count(self, dep):
        return len(dep.member_ids)
