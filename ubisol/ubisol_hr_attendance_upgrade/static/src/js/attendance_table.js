odoo.define('attendance_table.RenderTable',function (require) {
    "use strict";
    
    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var FormRenderer = require('web.FormRenderer');
    var viewRegistry = require('web.view_registry');
    var rpc = require('web.rpc');

    var EmployeeFormRenderer = FormRenderer.extend({

        /**
         * @override
         */
        _render: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var res = rpc.query({
                    model: 'hr.attendance',
                    method: 'get_my_attendances',
                }).then(function (data) {
                    self._renderTable(self, data)
                });
            });
        },

        destroy: function () {
            console.log('destroyed');
        },

        _renderTable: function(ev, attendances) {
            var $table = $('<table>').addClass('custom_attendance_table table table-sm table-hover table-striped');
            var $tbody = $('<tbody>');
            attendances.forEach(att => {
                var $tr = $('<tr/>', { class: 'o_data_row' });
                for (var key of Object.keys(att)) {
                    var $cell = $('<td>');
                    $cell.html(att[key]);
                    $tr.append($cell);
                }
                $tbody.append($tr);
            });
            $table.append($tbody);
            var $att_div = this.$el.find('.attendance_ids');
            $att_div.append($table);
            return true;
        },

        _renderRow: function (row) {
            var self = this;
            var $tr = $('<tr/>', { class: 'o_data_row' });
            row.forEach(cell => {
                var $cell = $('<td>');
                $cell.html(cell);
            });
            return $tr;
        },
    });

    var EmployeeFormController = FormController.extend({
        custom_events: _.extend({}, FormController.prototype.custom_events, {
            render_table: '_renderTable',
        }),

        _renderTable: function(ev) {
            var self = this;
            var res = rpc.query({
                model: 'hr.attendance',
                method: 'get_my_attendances',
            }).then(function (data) {
                return data;
            });
        },
    });

    var EmployeeFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: EmployeeFormController,
            Renderer: EmployeeFormRenderer
        }),
    });

    viewRegistry.add('hr_attendance_form', EmployeeFormView);
    return EmployeeFormView;
});