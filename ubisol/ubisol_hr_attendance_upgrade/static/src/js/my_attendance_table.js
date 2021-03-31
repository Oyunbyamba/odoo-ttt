odoo.define("my_attendance_table.RenderTable", function(require) {
  "use strict";

  var FormController = require("web.FormController");
  var FormView = require("web.FormView");
  var FormRenderer = require("web.FormRenderer");
  var viewRegistry = require("web.view_registry");
  var rpc = require("web.rpc");
  var core = require("web.core");
  var Dialog = require("web.Dialog");
  var framework = require("web.framework");

  var _t = core._t;

  function convertDateToTime(datetime) {
    var d = moment(datetime).add(8, "hours");
    if (d.isValid()) {
      var hour = d.format("HH");
      var minute = d.format("mm");
      return hour + ":" + minute;
    } else {
      return "-";
    }
  }

  function convertNumToTime(number) {
    // Check sign of given number
    var sign = number >= 0 ? 1 : -1;
    // Set positive value of number of sign negative
    number = number * sign;
    // Separate the int from the decimal part
    var hour = Math.floor(number);
    var decpart = number - hour;
    var min = 1 / 60;
    // Round to nearest minute
    decpart = min * Math.round(decpart / min);
    var minute = Math.floor(decpart * 60) + "";
    // Add padding if need
    if (minute.length < 2) {
      minute = "0" + minute;
    }
    // Add Sign in final result
    sign = sign == 1 ? "" : "-";
    // set HH format in hour
    hour = hour.toString().length >= 2 ? hour : `0${hour}`;
    // Concate hours and minutes
    var time = sign + hour + ":" + minute;
    return time;
  }

  function romanize(num) {
    if (isNaN(num)) return NaN;
    var digits = String(+num).split(""),
      key = [
        "",
        "C",
        "CC",
        "CCC",
        "CD",
        "D",
        "DC",
        "DCC",
        "DCCC",
        "CM",
        "",
        "X",
        "XX",
        "XXX",
        "XL",
        "L",
        "LX",
        "LXX",
        "LXXX",
        "XC",
        "",
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI",
        "VII",
        "VIII",
        "IX"
      ],
      roman = "",
      i = 3;
    while (i--) roman = (key[+digits.pop() + i * 10] || "") + roman;
    return Array(+digits.join("") + 1).join("M") + roman;
  }

  function changeDateFormat(val) {
    var d = moment(val, "YYYY-MM-DD", true);
    if (d.isValid()) {
      var month = d.format("M");
      var day = d.format("D");
      return romanize(month) + "/" + day;
    } else {
      return val;
    }
  }

  var EmployeeFormRenderer = FormRenderer.extend({
    /**
     * @override
     */
    _render: function() {
      var self = this;
      return this._super.apply(this, arguments).then(function() {
        var filters = {};
        if (!self.state.data.employee_id) {
          Dialog.alert(
            self,
            _t("Энэ хэрэглэгч дээр ажилтан холбоогүй байна!"),
            {
              confirm_callback: function() {
                framework.redirect("/");
              },
              title: _t("Анхааруулга")
            }
          );
        } else {
          filters["calculate_type"] = "employee";
          filters["employee_id"] = self.state.data.employee_id.data.id;
          filters["start_date"] = self.state.data.start_date;
          filters["end_date"] = self.state.data.end_date;

          var res = rpc
            .query({
              model: "hr.attendance.report",
              method: "get_my_attendances_report",
              args: [filters]
            })
            .then(function(data) {
              var count_table = 1;
              data.forEach(dat => {
                self._renderTable(self, dat, count_table);
                count_table++;
              });
            });
        }
      });
    },

    autofocus: function() {
      var self = this;
      var node = window.$("div.o_form_buttons_edit");
      node.hide();

      window.$(".breadcrumb li").remove();

      var new_li = $("<li></li>").addClass("breadcrumb-item active");
      new_li.text("Миний ирц");
      new_li.appendTo("ol.breadcrumb");

      return this._super();
    },

    destroy: function() {
      this._super();
    },

    _renderTable: function(ev, data, count_table) {
      var $table = $("<table>").addClass(
        "table table-sm table-hover table-bordered table-striped"
      );
      var $thead = $("<thead>");
      var $tbody = $("<tbody>");
      var headers = data.header;
      var fields = data.fields;
      var rows = data.data;
      var child_employees = data.child_employees;

      var $tr = $("<tr/>", { class: "o_data_row" });
      $tr.css({ "background-color": "#eee" });
      headers.forEach(h => {
        if (h[0] == "field_name") {
          var $cell = $("<th>");
          $cell.css({
            "background-color": "#eee",
            position: "sticky",
            top: "0"
          });
          $cell.html("#");
          $tr.append($cell);

          if (count_table == 2) {
            $cell = $("<th>");
            $cell.css({
              "background-color": "#eee",
              position: "sticky",
              top: "0"
            });
            $cell.html("Нийт цаг");
            $tr.append($cell);
          }
        } else {
          var $cell = $("<th>");
          if (h[1] == 1) {
            $cell.css({
              "background-color": "#99d5ff",
              position: "sticky",
              top: "0"
            });
          } else {
            $cell.css({
              "background-color": "#eee",
              position: "sticky",
              top: "0"
            });
          }
          $cell.html(changeDateFormat(h[0]));
          $tr.append($cell);
        }
      });
      $thead.append($tr);
      $table.append($thead);

      //only self attandance calculations
      if (count_table == 1) {
        rows.forEach((att, i) => {
          var $tr = $("<tr/>", { class: "o_data_row" });
          for (var header of headers) {
            var key = header[0];
            switch (key) {
              case "id":
              case "__count":
                break;
              case "field_name":
                var cell = att[key];
                var $cell = $("<td>");
                $cell.html(cell);
                $tr.append($cell);
                break;
              default:
                var cell = att[key][0];
                if (cell) {
                  var $cell = $("<td>");
                  if (
                    fields[i][0] == "check_in" ||
                    fields[i][0] == "check_out"
                  ) {
                    var hours = convertDateToTime(cell[fields[i][0]]);
                    if (hours == "-") {
                      $cell.css({ "background-color": "#ffb3b4" });
                    }
                  } else {
                    var hours = convertNumToTime(cell[fields[i][0]]);
                  }
                  $cell.html(hours);
                  if (header[1] == 1) {
                    $cell.css({ "background-color": "#99d5ff" });
                  }
                  $tr.append($cell);
                } else {
                  var hours = "-";
                  var $cell = $("<td>");
                  $cell.html(hours);
                  if (header[1] == 1) {
                    $cell.css({ "background-color": "#99d5ff" });
                  }
                  $tr.append($cell);
                }

                break;
            }
          }
          $tbody.append($tr);
        });
      }

      $table.append($tbody);

      var $att_div = this.$el.find(".my_attendances_table");
      var $div_el =
        count_table == 1
          ? $("<div>").css({ "overflow-x": "scroll", "margin-bottom": "15px" })
          : $("<div>").css({ "overflow-y": "scroll", "max-height": "310px" });
      $att_div.css({ "max-height": "600px", width: "100%" });
      $table = $table.css({ "margin-bottom": "1px" });
      $div_el.append($table);
      $att_div.append($div_el);

      return true;
    },

    _renderRow: function(row) {
      var self = this;
      var $tr = $("<tr/>", { class: "o_data_row" });
      row.forEach(cell => {
        var $cell = $("<td>");
        $cell.html(cell);
      });
      return $tr;
    }
  });

  var EmployeeFormController = FormController.extend({
    custom_events: _.extend({}, FormController.prototype.custom_events, {
      render_table: "_renderTable"
    }),

    _renderTable: function(ev) {
      // var self = this;
      // var res = rpc.query({
      //     model: 'hr.attendance',
      //     method: 'get_my_attendances',
      //     args: [ev.data.employee_id],
      // }).then(function (data) {
      //     return data;
      // });
    }
  });

  var EmployeeFormView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {
      Controller: EmployeeFormController,
      Renderer: EmployeeFormRenderer
    })
  });

  viewRegistry.add("hr_attendance_form", EmployeeFormView);
  return EmployeeFormView;
});
