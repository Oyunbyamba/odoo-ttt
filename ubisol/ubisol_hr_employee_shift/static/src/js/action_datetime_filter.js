odoo.define('action_datetime_filter.JsCalculateDate', function (require) {
    "use strict";
    
    var ListController = require('web.ListController');
    var rpc = require('web.rpc');
    var res = rpc.query({
        model: 'hr.employee.schedule',
        method: 'get_departments',
    }).then(function (data) {
        setTimeout(() => {
            data.forEach(d => {
                // $('#departments').append(`<option value="${d.value}">${d.label}</option>`); 
                var deps = document.getElementById("departments");
                var option = document.createElement("option");
                option.value = d.value;
                option.text = d.label;
                deps.add(option);
                // $('#departments').append($("<option></option>").attr("value", d.value).text(d.label)); 
            });
        }, 1000);
    });

    var JsCalculateDate = ListController.include({
        renderButtons: function($node){
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.on('click', '.o_button_calculate_date', this.action_to_call_wizard.bind(this));
                this.$buttons.appendTo($node);
            }
        },
        action_to_call_wizard: function(event) {
            event.preventDefault();
            var self = this;
            var departments = $( "#departments" ).val();
            var date1 = $( "#date1" ).val();
            var date2 = $( "#date2" ).val();



            alert(date1 + '  ' + date2);
            alert(departments);
        },
    });
    
    // var JsTocallWizard = ListController.include({
    //     renderButtons: function($node){
    //         this._super.apply(this, arguments);
    //         if (this.$buttons) {
    //             this.$buttons.on('click', '.o_button_to_call_wizard', this.action_to_call_wizard.bind(this));
    //             this.$buttons.appendTo($node);
    //         }
    //     },
    //     action_to_call_wizard: function(event) {
    //         event.preventDefault();
    //         var self = this;
    //         self.do_action({
    //             name: "Хугацааны интервал",
    //             type: 'ir.actions.act_window',
    //             res_model: 'create.datetime.filter',
    //             view_mode: 'form',
    //             view_type: 'form',
    //             views: [[false, 'form']],
    //             target: 'new',
    //         });
        
    //     },
    // });
});