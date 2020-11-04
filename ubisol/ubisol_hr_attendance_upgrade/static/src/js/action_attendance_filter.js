odoo.define('action_attendance_filter.JsTocallAttendanceWizard',function (require) {
    "use strict";
    
    var ListController = require('web.ListController');
    
    var JsTocallAttendanceWizard = ListController.include({
        renderButtons: function($node){
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.on('click', '.o_button_to_call_attendance_wizard', this.action_to_call_attendance_wizard.bind(this));
                this.$buttons.appendTo($node);
            }
        },
        action_to_call_attendance_wizard: function(event) {
            event.preventDefault();
            var self = this;
            self.do_action({
                name: "Хугацааны интервал",
                type: 'ir.actions.act_window',
                res_model: 'create.attendance.filter',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
            });
        
        },
    });
});