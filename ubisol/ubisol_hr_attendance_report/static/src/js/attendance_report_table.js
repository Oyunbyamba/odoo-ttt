odoo.define('attendance_report_table.RenderTable',function (require) {
    "use strict";
    
    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var FormRenderer = require('web.FormRenderer');
    var viewRegistry = require('web.view_registry');
    var rpc = require('web.rpc');

    function convertNumToTime(number) {
        var sign = (number >= 0) ? 1 : -1;
        number = number * sign;
        var hour = Math.floor(number);
        var decpart = number - hour;
        var min = 1 / 60;
        decpart = min * Math.round(decpart / min);
        var minute = Math.floor(decpart * 60) + '';
        if (minute.length < 2) {
            minute = '0' + minute; 
        }
        sign = sign == 1 ? '' : '-';
        var time = sign + hour + ':' + minute;
        return time;
    }

    var EmployeeFormRenderer = FormRenderer.extend({

        /**
         * @override
         */
        _render: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var filters = {};
                filters['calculate_type'] = self.state.data.calculate_type;
                if (self.state.data.calculate_type) {
                    if (self.state.data.calculate_type == 'employee') {
                        filters['employee_id'] = self.state.data.employee_id.data.id;
                    } else {
                        filters['department_id'] = self.state.data.department_id.data.id;
                    }
                }
                filters['start_date'] = self.state.data.start_date;
                filters['end_date'] = self.state.data.end_date;
                
                var res = rpc.query({
                    model: 'hr.attendance.report',
                    method: 'get_attendances_report',
                    args: [filters],
                }).then(function (data) {
                    self._renderTable(self, data)
                });
            });
        },

        autofocus: function () {
            var self = this;

            var button = window.$('#attendance_report_download');
            button.css({"margin-left": "8px"})

            var node = window.$('div.o_form_buttons_edit');
            node.hide();

            window.$(".breadcrumb li").remove();

            var new_li = $('<li></li>').addClass('breadcrumb-item active');
            new_li.text('Ирцийн график');
            new_li.appendTo('ol.breadcrumb');

            return this._super();
        },

        destroy: function () {
            this._super();
        },

        _renderTable: function(ev, data) {
            var $table = $('<table>').addClass('table table-sm table-hover table-bordered table-striped');
            var $thead = $('<thead>');
            var $tbody = $('<tbody>');
            var headers = data.header;
            var rows = data.data;

            var $tr = $('<tr/>', { class: 'o_data_row' });
            $tr.css({"background-color": "#d9d9d9"})
            headers.forEach(h => {
                var $cell = $('<th>');
                $cell.css({"position": "sticky", "top": "0"})
                $cell.html(h[1]);
                $tr.append($cell);
            });
            $thead.append($tr);
            $table.append($thead);

            rows.forEach(att => {
                var $tr = $('<tr/>', { class: 'o_data_row' });
                var i = 0;
                for (var header of headers) {
                    var key = header[0];
                    switch (key) {
                        case 'id':
                        case '__count':
                            break;
                        case 'take_off_day':
                        case 'work_days':
                        case 'worked_days':
                            var $cell = $('<td>');
                            $cell.html(att[key]);
                            $tr.append($cell);
                            break;
                        case 'hr_employee_shift':
                            var $cell = $('<td>');
                            $cell.html(att[key][1]);
                            $tr.append($cell);
                            break;
                        case 'full_name':
                            var $cell = $('<th>');
                            $cell.css({"background-color": "#f2f2f2"})
                            $cell.html(att[key]);
                            $tr.append($cell);
                            break;
                        default:
                            var hours = convertNumToTime(att[key]);
                            var $cell = $('<td>');
                            $cell.html(hours);
                            $tr.append($cell);
                            break;
                    }
                }
                $tbody.append($tr);
            });
            $table.append($tbody);

            var $att_div = this.$el.find('.attendance_report');
            $att_div.css({"max-height": "600px", "overflow-y": "scroll", "overflow-x": "scroll", "max-width": "95%"})
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