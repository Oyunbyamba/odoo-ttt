odoo.define('attendance_report_table.RenderTable',function (require) {
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
                var filters = {};
                var today = new moment().format('YYYY-MM-DD');
                if(moment().date() > 20) {
                    var prevMonth = new moment().set("date", 20).format('YYYY-MM-DD');
                } else {
                    var prevMonth = new moment().subtract(1, 'months').set("date", 20).format('YYYY-MM-DD');
                }
                if(typeof self.state.data.employee_id === 'undefined') {
                    console.log('employee_id not have');
                } else {
                    console.log('employee_id have');
                }
                if (typeof self.state.data.start_date === 'undefined') {
                    filters['start_date'] = today;
                } else {
                    filters.push();
                }
                if (typeof self.state.data.end_date === 'undefined') {
                    filters['end_date'] = prevMonth;
                } else {
                    filters.push();
                }
                
                var res = rpc.query({
                    model: 'hr.attendance.report',
                    method: 'get_attendances_report',
                    args: [filters],
                }).then(function (data) {
                    self._renderTable(self, data)
                });
            });
        },

        destroy: function () {
            console.log('destroyed');
        },

        _renderTable: function(ev, data) {
            var $table = $('<table>').addClass('custom_attendance_table table table-sm table-hover table-striped');
            var $thead = $('<thead>');
            var $tbody = $('<tbody>');
            var headers = data.header;
            var rows = data.data;

            console.log('headers: ', headers);
            console.log('rows: ', rows);

            var $tr = $('<tr/>', { class: 'o_data_row' });
            headers.forEach(h => {
                var $cell = $('<th>');
                $cell.html(h);
                $tr.append($cell);
            });
            $thead.append($tr);
            $table.append($thead);

            rows.forEach(att => {
                var $tr = $('<tr/>', { class: 'o_data_row' });
                var i = 0;
                for (var key of Object.keys(att)) {
                    var $cell = $('<td>');
                    $cell.html(att[key]);
                    $tr.append($cell);
                }
                $tbody.append($tr);
            });
            $table.append($tbody);

            var $att_div = this.$el.find('.attendance_report');
            $att_div.css({"max-height": "600px", "overflow-y": "scroll"})
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
            // var self = this;
            // var res = rpc.query({
            //     model: 'hr.attendance',
            //     method: 'get_my_attendances',
            //     args: [ev.data.employee_id],
            // }).then(function (data) {
            //     return data;
            // });
        },
    });

    var EmployeeFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: EmployeeFormController,
            Renderer: EmployeeFormRenderer
        }),
    });

    viewRegistry.add('hr_attendance_report_form', EmployeeFormView);
    return EmployeeFormView;
});