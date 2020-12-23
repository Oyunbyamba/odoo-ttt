odoo.define('biometric_attendance.JsToCallBiometricWizard',function (require) {
    "use strict";
    
    var ListController = require('web.ListController');
    
    var JsToCallBiometricWizard = ListController.include({
        renderButtons: function($node){
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.on('click', '.o_button_to_call_biometric_wizard', this.action_to_call_attendance_wizard.bind(this));
                this.$buttons.appendTo($node);
            }
        },
        action_to_call_attendance_wizard: function(event) {
            event.preventDefault();
            var self = this;
            self.do_action({
                name: "Тооцоолол",
                type: 'ir.actions.act_window',
                res_model: 'biometric.attendance.wizard',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
            });
        
        },
    });
});