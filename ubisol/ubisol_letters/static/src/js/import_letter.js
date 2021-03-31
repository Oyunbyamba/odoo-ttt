odoo.define('ubisol_letter.importLetter',function (require) {
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
                this.$buttons.on('click', '.oe_import_letter', this.action_to_call_import_letter.bind(this));
                this.$buttons.appendTo($node);
            }
        },
        action_to_call_import_letter: function(event) {
            event.preventDefault();
            var self = this;
            var user = session.uid;

            rpc.query({
                model: 'ubi.letter',
                method: 'model_function',
                args: [[user],{'id':user}],
            }).then(function (e) {
                self.do_action({
                    name: _t('Ирсэн бичиг'),
                    type: 'ir.actions.act_window',
                    res_model: 'ubi.letter',
                    views: [[false,tree,form]],
                    view_mode: 'tree,form'
                });
            });
        
        },
    });
});