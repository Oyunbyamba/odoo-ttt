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
                name: "Шүүлтүүр",
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