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

{
    'name': 'Web Multi-column Ordering',
    'version': '1.0',
    'category': 'Added functionality',
    'description': """
InfoSreda OpenERP Web Multi-column Ordering
===========================================

OpenERP web-client extension that allows sorting tree views by multiple columns. Module replaces all OpenERP tree views in web-client with ordering by multiple columns capabilities instead of single column sorting.

Usage
=====

* First click by column header makes ascending ordering for the column (first level)
* Click other column header to make ordering by that column either (second level)
* etc...
* Continue clicking at the column header in order to cycle through ascending, descending and "no sorting at all" modes

Ordering mode of the concrete column is intuitively presented as mark at the column header. This mark displays sorting level number and direction.
""",
    'author': 'Infosreda LLC',
    'website': 'http://www.infosreda.com/',
    'depends': ['base'],
    'init_xml': [],
    'update_xml': [],
    'installable': True,
    'active': False,
    'web': True,
    'images': ['images/web_multicolumnordering.png'],
}
