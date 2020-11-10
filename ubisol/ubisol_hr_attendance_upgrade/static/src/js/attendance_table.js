odoo.define('attendance_table.RenderTable',function (require) {
    "use strict";
    
    var FormController = require('web.FormController');
    var FormView = require('web.FormView');
    var FormRenderer = require('web.FormRenderer');
    var viewRegistry = require('web.view_registry');
    var rpc = require('web.rpc');

    function convertNumToTime(number) {
        // Check sign of given number
        var sign = (number >= 0) ? 1 : -1;
        // Set positive value of number of sign negative
        number = number * sign;
        // Separate the int from the decimal part
        var hour = Math.floor(number);
        var decpart = number - hour;
        var min = 1 / 60;
        // Round to nearest minute
        decpart = min * Math.round(decpart / min);
        var minute = Math.floor(decpart * 60) + '';
        // Add padding if need
        if (minute.length < 2) {
            minute = '0' + minute; 
        }
        // Add Sign in final result
        sign = sign == 1 ? '' : '-';
        // Concate hours and minutes
        var time = sign + hour + ':' + minute;
        return time;
    }

    function romanize (num) {
        if (isNaN(num))
            return NaN;
        var digits = String(+num).split(""),
            key = ["","C","CC","CCC","CD","D","DC","DCC","DCCC","CM",
                   "","X","XX","XXX","XL","L","LX","LXX","LXXX","XC",
                   "","I","II","III","IV","V","VI","VII","VIII","IX"],
            roman = "",
            i = 3;
        while (i--)
            roman = (key[+digits.pop() + (i * 10)] || "") + roman;
        return Array(+digits.join("") + 1).join("M") + roman;
    }

    function changeDateFormat(val) {
        var d = moment(val, "YYYY-MM-DD", true);
        if(d.isValid()) {
            var month = d.format('M');
            var day   = d.format('D');
            return romanize(month) + '/' + day;
        } else {
            return val;
        }
    }

    var EmployeeFormRenderer = FormRenderer.extend({

        /**
         * @override
         */
        _render: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                var filters = {};
                filters['calculate_type'] = 'employee';
                filters['employee_id'] = self.state.data.employee_id.data.id;
                filters['start_date'] = self.state.data.start_date;
                filters['end_date'] = self.state.data.end_date;

                console.log(filters);
                
                var res = rpc.query({
                    model: 'hr.attendance.report',
                    method: 'get_my_attendances_report',
                    args: [filters],
                }).then(function (data) {
                    self._renderTable(self, data)
                });
            });
        },

        autofocus: function () {
            var self = this;
            var node = window.$('div.o_form_buttons_edit');
            node.hide();
            return this._super();
        },

        destroy: function () {
            this._super();
        },

        _renderTable: function(ev, data) {
            var $table = $('<table>').addClass('custom_attendance_table table table-sm table-hover table-striped');
            var $thead = $('<thead>');
            var $tbody = $('<tbody>');
            var headers = data.header;
            var fields = data.fields;
            var rows = data.data;

            console.log('headers: ', headers);
            console.log('rows: ', rows);

            var $tr = $('<tr/>', { class: 'o_data_row' });
            $tr.css({"background-color": "#eee"})
            headers.forEach(h => {
                var $cell = $('<th>');
                $cell.css({"background-color": "#eee", "position": "sticky", "top": "0"})
                $cell.html(changeDateFormat(h));
                $tr.append($cell);
            });
            $thead.append($tr);
            $table.append($thead);

            rows.forEach((att, i) => {
                var $tr = $('<tr/>', { class: 'o_data_row' });
                for (var header of headers) {
                    var key = header;
                    switch (key) {
                        case 'id':
                        case '__count':
                            break;
                        case 'field_name':
                            var cell = att[key];
                            var $cell = $('<td>');
                            $cell.html(cell);
                            $tr.append($cell);
                            break;
                        default:
                            if (!att[key]) {
                                console.log(key, att);
                                break;
                            }
                            var cell = att[key][0];
                            var hours = convertNumToTime(cell[fields[i]]);
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
            $att_div.css({"max-height": "600px", "width": "100%", "overflow-x": "scroll"})
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

    viewRegistry.add('hr_attendance_form', EmployeeFormView);
    return EmployeeFormView;
});