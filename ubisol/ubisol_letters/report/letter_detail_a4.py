import logging
from datetime import date, datetime, timedelta, time
from odoo.exceptions import UserError
from odoo import api, models, _

_logger = logging.getLogger(__name__)


class letterDetailPdf(models.AbstractModel):
    _name = 'report.ubisol_letters.letter_detail_report_a4'
    _description = 'Employee Letter Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['ubi.letter.going'].browse(docids)
        employee = self.env.user.employee_id
        now_date = (datetime.now()).strftime('%Y-%m-%d')

        # report = self.env['ir.actions.report']._get_report_from_name(
        #     'ubisol_letters.letter_detail_report_a5')
        # report.paperformat_id = self.env.ref(
        #     'ubisol_letters.letter_paperformat')

        report = self.env.ref('ubisol_letters.letter_detail_report_a4_pdf')
        report.paperformat_id = self.env.ref(
            'ubisol_letters.letter_paperformat').id
        # paperformat_obj = self.env.ref('ubisol_letters.letter_paperformat').id
        # _logger.info(paperformat_obj)

        # report_obj = self.env['ir.actions.report']
        # report = report_obj._get_report_from_name(
        #     'ubisol_letters.letter_detail_report_a4')
        # self.paperformat_id = self.env.ref(
        #    'ubisol_letters.letter_paperformat').id

        data = {
            'now_date': now_date,
            'docs': docs,
            'doc_model': report.model,
            'employee': employee[0]
        }
        return report.report_action([], data=data)

    # @api.model
    # def get_paperformat(self):
    #     # return self.paperformat_id or self.env.company.paperformat_id
    #     return self.env.ref('ubisol_letters.letter_paperformat').id
