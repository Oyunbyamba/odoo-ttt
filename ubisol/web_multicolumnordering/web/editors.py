# -*- coding: utf-8 -*-

##############################################################################
#
#    Author Boris Timokhin. Copyright InfoSreda LLC
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openobject.templating import TemplateEditor


class BaseTemplateEditor(TemplateEditor):
    templates = ['/openobject/controllers/templates/base.mako']
    
    def edit(self, template, template_text):
        output = super(BaseTemplateEditor, self).edit(template, template_text)
        
        end_head = output.index('</head>')
        
        output = output[:end_head] + """
            <script type="text/javascript" src="/web_multicolumnordering/static/javascript/multicolumn_ordering.js"></script>
""" + output[end_head:]
        
        return output
