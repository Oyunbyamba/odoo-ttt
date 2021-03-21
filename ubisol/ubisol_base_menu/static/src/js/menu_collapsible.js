odoo.define('web_menu_collapsible.Menu', function(require) {
"use strict";
    
    var Menu = require('web.Menu');

    Menu.include({
        start: function() {
            var self = this;
            console.log('menu js 1');
            $(".dropdown-item").hide();
            $(".dropdown-header").each(function() {
                if($(this).next().hasClass('dropdown-item')) {
                    $(this).unbind("click");
                    $(this).click(self.section_clicked);
                    $(this).addClass('oe_menu_toggler');
                }
            });
            return this._super.apply(this, arguments);
        },
        section_clicked: function() {
            $(this).toggleClass('oe_menu_opened').next().toggle();
        }
    });
});
