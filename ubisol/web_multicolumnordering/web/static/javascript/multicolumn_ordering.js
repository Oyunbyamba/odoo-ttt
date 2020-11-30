/* #############################################################################
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
############################################################################# */

$(function() {
	var ListView = window.ListView;
	
	if (typeof ListView === 'undefined')
		return;
	
	ListView.prototype.orderState = [];
	
	ListView.prototype.sort_by_order = function(column, field) {
		var needAdd = true, elementState;
		
		for (var i=0; i < this.orderState.length; i++) {
			elementState = this.orderState[i];
			if (elementState.column == column) {
				needAdd = false;
			
				if (elementState.dir == 'desc') {
					this.orderState.splice(i, 1);
					i--;
					continue;
				}
			
				if (elementState.dir == 'asc') {
					this.orderState[i].dir = 'desc';
				}
			}
		};
	
		if (needAdd)
			this.orderState.push({'column':column, 'dir': 'asc'});
		
		if (this.ids.length)
			this.reload();
	};

ListView.prototype.reload = function(edit_inline, concurrency_info, default_get_ctx, clear) {
	if (openobject.http.AJAX_COUNT > 0)
		return callLater(1, bind(this.reload, this), edit_inline, concurrency_info);
		
		var self = this;
		
		var current_id = edit_inline ? (parseInt(edit_inline) || 0) : edit_inline;
		
		var args = jQuery.extend(this.makeArgs(), {
			_terp_source: this.name,
			_terp_edit_inline: edit_inline,
			_terp_source_default_get: default_get_ctx,
			_terp_concurrency_info: concurrency_info,
			_terp_editable: openobject.dom.get('_terp_editable').value,
			_terp_group_by_ctx: openobject.dom.get('_terp_group_by_ctx').value
		});
		
		if (this.name == '_terp_list') {
			jQuery.extend(args, {
				_terp_search_domain: openobject.dom.get('_terp_search_domain').value,
				_terp_search_data: openobject.dom.get('_terp_search_data').value,
				_terp_filter_domain: openobject.dom.get('_terp_filter_domain').value
		});
	}
	
	if (this.orderState.length) {
		var sort_key = [], columnOrder;
		for (var i=0, l=this.orderState.length; i<l;i++) {
			columnOrder = this.orderState[i].column
			if (i == l - 1)
				var _sort_order = this.orderState[i].dir;
			else
				if (this.orderState[i].dir == 'desc')
					columnOrder += ' ' + this.orderState[i].dir;
				sort_key.push(columnOrder);
		};
		
		jQuery.extend(args, {
			_terp_sort_key: sort_key.join(', '),
			_terp_sort_order: _sort_order
		});
	};
	
	if(clear) {
		args['_terp_clear'] = true;
	}
	
	jQuery(idSelector(self.name) + ' .loading-list').show();
	jQuery.ajax({
		url: '/openerp/listgrid/get',
		data: args,
		dataType: 'jsonp',
		type: 'POST',
		error: loadingError(),
		success: function(obj) {
			var _terp_id = openobject.dom.get(self.name + '/_terp_id') || openobject.dom.get('_terp_id');
			var _terp_ids = openobject.dom.get(self.name + '/_terp_ids') || openobject.dom.get('_terp_ids');
			var _terp_count = openobject.dom.get(self.name + '/_terp_count') || openobject.dom.get('_terp_count');
			_terp_id.value = current_id > 0 ? current_id : 'False';
			
			if (obj.ids) {
				if (typeof(current_id) == "undefined" && obj.ids.length) {
					current_id = obj.ids[0];
				}
				
				_terp_id.value = current_id > 0 ? current_id : 'False';
				_terp_ids.value = self.ids = '[' + obj.ids.join(',') + ']';
				_terp_count.value = obj.count;
			}
			
			self.current_record = edit_inline;
			
			if(obj.logs) {
				jQuery('div#server_logs').replaceWith(obj.logs)
			}
			
			var $list = jQuery(idSelector(self.name));
			$list.empty().trigger('before-redisplay');
			
			if(clear) {
				jQuery('#view_form').replaceWith(obj.view);
				initialize_search();
			} else {
				var __listview = openobject.dom.get(self.name).__listview;
				$list.parent().replaceWith(obj.view);
			}
			
			var $editors = self.$adjustEditors(
				document.getElementById(self.name)
			);
			
			if ($editors.length > 0)
				self.bindKeyEventsToEditors($editors);
			
			openobject.dom.get(self.name).__listview = __listview;
			
			var first = jQuery('input.listfields')[0] || null;
			
			if (first) {
				first.focus();
				first.select();
			}
			
			if ($editors.length && edit_inline == -1) {
				$editors.each(function () {
					var $this = jQuery(this);
					if ($this.val() && $this.attr('callback'))
						MochiKit.Signal.signal(this, 'onchange');
				});
			}
			
			MochiKit.Signal.signal(__listview, 'onreload');
			
			if ( self.orderState.length ) {
				for (var i=0, l=self.orderState.length; i<l; i++ ) {
					var $th,
					element = self.orderState[i];
					if(self.name != '_terp_list') {
						$th = jQuery(idSelector('grid-data-column/' + self.name + '/' + element.column));
					} else {
						$th = jQuery(idSelector('grid-data-column/' + element.column));
					}
					$th.append(
						jQuery('<span>&nbsp;</span>')
					).append(
						jQuery('<img>', {
							style: "vertical-align: middle;",
							class: element.dir,
							src: '/openerp/static/images/listgrid/' + (
								element.dir == 'asc' ? 'arrow_down.gif' : 'arrow_up.gif'
							)
						}))
						.append(" <span style=\"font-size: .8em;\">(" + (i + 1) + ")</span>");
				}
			}
			
			updateConcurrencyInfo(obj.concurrency_info || {});
		} // ajax success
	}); //ajax
}});
