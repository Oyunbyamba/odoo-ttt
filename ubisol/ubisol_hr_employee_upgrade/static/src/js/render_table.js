odoo.define('render_table.RenderTable',function (require) {
    "use strict";
    
    var FormController = require('web.FormController');

    // var txt1 = "<p>Text.</p>";
    // var txt2 = $("<p></p>").text("Text.");
    // $("#attendance_ids").append(txt1, txt2);

    var RenderTable = FormController.include({
        // init: function () {
        //     console.log('here i go');
        // },
        // renderButtons: function($node){
        //     this._super.apply(this, arguments);
        //     if (this.$buttons) {
        //         this.$buttons.on('click', '.o_button_to_call_wizard', this.action_to_call_wizard.bind(this));
        //         this.$buttons.appendTo($node);
        //     }
        // },
        // action_to_call_wizard: function(event) {
        //     event.preventDefault();
        //     var self = this;
        //     self.do_action({
        //         name: "Хугацааны интервал",
        //         type: 'ir.actions.act_window',
        //         res_model: 'create.datetime.filter',
        //         view_mode: 'form',
        //         view_type: 'form',
        //         views: [[false, 'form']],
        //         target: 'new',
        //     });
        
        // },
    });
});