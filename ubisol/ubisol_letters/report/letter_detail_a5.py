import logging
from datetime import date, datetime, timedelta, time
from odoo.exceptions import UserError
from odoo import api, models, _

_logger = logging.getLogger(__name__)


class letterDetailPdf(models.AbstractModel):
    _name = 'report.ubisol_letters.letter_detail_report_a5'
    _description = 'Employee Letter Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['ubi.letter.going'].browse(docids)
        employee = self.env.user.employee_id
        now_date = (datetime.now()).strftime('%Y-%m-%d')

        _logger.info('report a5')
        _logger.info(self)
        _logger.info(docids)
        _logger.info(data)
        _logger.info(employee)
        return {
                'now_date': now_date,
                'docs': docs,
                'employee': employee
            }