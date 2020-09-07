var employee_data = [];

var nodeTemplate = function (data) {
  return `
        <span class="office">${data.office}</span>
        <div class="title">${data.name}</div>
        <div class="content">${data.title}</div>
      `;
};

odoo.define("org_chart_employee.org_chart", function (require) {
  "use strict";

  var AbstractAction = require("web.AbstractAction");
  var core = require("web.core");
  var session = require("web.session");
  var ajax = require("web.ajax");
  var QWeb = core.qweb;
  var _t = core._t;
  var _lt = core._lt;

  var OrgChartDepartment = AbstractAction.extend({
    hasControlPanel: true,
    init: function (parent, context) {
      this._super(parent, context);
      var self = this;
      console.log("self");
      console.log(self);
      if (context.tag == "org_chart_employee.org_chart_department") {
      }
    },
    retch_data: function () {
      var self = this;
      this._rpc({
        model: "org.chart.employee",
        method: "get_employee_data",
      }).then(function (result) {
        employee_data = result;
        self.render();
        self.href = window.location.href;
      });
      //.done(function () {});
    },
    willStart: function () {
      var self = this;
      self.retch_data();
      return $.when(ajax.loadLibs(this), this._super());
    },
    start: function () {
      var self = this;
      return this._super();
    },
    render: function () {
      var super_render = this._super;
      var self = this;
      var org_chart = QWeb.render("org_chart_employee.org_chart_template", {
        widget: self,
      });
      $(".o_control_panel").addClass("o_hidden");
      $(org_chart).prependTo(self.$el);
      return org_chart;
    },
    reload: function () {
      window.location.href = this.href;
    },
  });

  core.action_registry.add(
    "org_chart_employee.org_chart_department",
    OrgChartDepartment
  );

  return OrgChartDepartment;
});
