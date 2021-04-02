odoo.define('import_letter.importLetter',function (require) {
    "use strict";

    var core = require('web.core');
    var ListController = require('web.ListController');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var _t = core._t;

    var importLetter = ListController.include({
        renderButtons: function($node){
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.on('click', '.o_button_to_call_import_letter', this.action_to_call_import_letter.bind(this));
                this.$buttons.appendTo($node);
            }
        },
        action_to_call_import_letter: function(event) {
            // event.preventDefault();
            var self = this;
            var user = session.uid;
            console.log('check_connection_function')
            rpc.query({
                model: 'ubi.letter',
                method: 'check_connection_function',
                args: [user],
            }).then(function (data) {
                alert(data);
                // self.do_action({
                //     name: _t('Ирсэн бичиг'),
                //     type: 'ir.actions.act_window',
                //     res_model: 'ubi.letter',
                //     views: [[false, 'list'], [false, 'form']],
                //     view_mode: "list",
                //     target: 'current'
                // });
            });

        },
    });
});
