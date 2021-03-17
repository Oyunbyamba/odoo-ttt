odoo.define('render_table.RenderTable',function (require) {
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
                // var $att_div = self.$el.find('.my_attendance_ids');
                // var txt1 = "<p>Text.</p>";
                // var txt2 = $("<p></p>").text("Text.");
                // $att_div.append(txt1, txt2);

                var employee_id = self.state.data.id;
                if(employee_id) {
                    self._renderTable(self)
                }
            });
        },

        autofocus: function () {
            var self = this;

            return this._super();
        },

        destroy: function () {
            console.log('destroyed');
        },

        _renderTable: function(ev) {
            this.trigger_up('render_table', {
                employee_id: this.state.data.id
            });
            return true;
        },
    });

    var EmployeeFormController = FormController.extend({
        custom_events: _.extend({}, FormController.prototype.custom_events, {
            render_table: '_renderTable'
        }),

        _renderTable: function(ev) {
            var self = this;
            var res = rpc.query({
                model: 'hr.employee',
                method: 'get_my_attendances',
                args: [ev.data.employee_id],
            }).then(function (data) {
                // console.log(data);
            });
        },
    });

    var EmployeeFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: EmployeeFormController,
            Renderer: EmployeeFormRenderer
        }),
    });

    viewRegistry.add('hr_employee_form', EmployeeFormView);
    return EmployeeFormView;
});