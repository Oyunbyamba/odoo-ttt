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

        paperformat_obj = self.env.ref('ubisol_letters.letter_paperformat').id
        _logger.info(paperformat_obj)

        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('ubisol_letters.letter_detail_report_a4')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
            'employee': employee
        }
        return docargs

    @api.model
    def get_paperformat(self):
        # return self.paperformat_id or self.env.company.paperformat_id
        return self.env.ref('ubisol_letters.letter_paperformat').id

