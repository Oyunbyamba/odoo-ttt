odoo.define('action_datetime_filter.JsCalculateDate',function (require) {
    "use strict";
    
    var ListController = require('web.ListController');
    var rpc = require('web.rpc');

    var res = rpc.query({
        model: 'hr.employee.schedule',
        method: 'get_departments',
    });

    var now = new Date();
    var day = ("0" + now.getDate()).slice(-2);
    var month = ("0" + (now.getMonth() + 1)).slice(-2);
    var lastMonth = now.getFullYear()+"-"+(month-1)+"-"+('20');
    var today = now.getFullYear()+"-"+(month)+"-"+(day);
    setTimeout(() => {
        $('#date1').val(lastMonth);
        $('#date2').val(today);
    }, 2000);

    res.then(function (data) {
        setTimeout(() => {
            data.forEach(d => {
                $('#departments').append($("<option></option>").attr("value", d.value).text(d.label)); 
            });
        }, 2000);
    });

    var JsCalculateDate = ListController.include({
        renderButtons: function($node){
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.on('click', '.o_button_calculate_date', this.action_calculate_date.bind(this));
                this.$buttons.appendTo($node);
            }
        },
        action_calculate_date: function(event) {
            event.preventDefault();
            var self = this;

            var date1 = $( "#date1" ).val();
            var date2 = $( "#date2" ).val();
            var departments = $( "#departments" ).val();
            date2 = $("#date2").datepicker({dateFormat: 'dd-mm-yyyy'});

            self.do_action({
                name: "Ажиллах график",
                type: "ir.ui.view",
                res_model: "hr.employee.schedule",
                context: {"search_default_department":1, "search_default_employee":1, "search_default_is_rest":1},
                view_mode: "tree,timeline,calendar",
                view_type: "tree",
              });
        },
    });
});

odoo.define('action_datetime_filter.JsTocallWizard',function (require) {
    "use strict";
    
    var ListController = require('web.ListController');
    
    var JsTocallWizard = ListController.include({
        renderButtons: function($node){
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.on('click', '.o_button_to_call_wizard', this.action_to_call_wizard.bind(this));
                this.$buttons.appendTo($node);
            }
        },
        action_to_call_wizard: function(event) {
            event.preventDefault();
            var self = this;
            self.do_action({
                name: "Хугацааны интервал",
                type: 'ir.actions.act_window',
                res_model: 'create.datetime.filter',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
            });
        
        },
    });
});