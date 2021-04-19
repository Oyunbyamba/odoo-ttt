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

        _logger.info('report a4')
        _logger.info(self)
        _logger.info(docids)
        if any(letter.paper_size in ['a5'] for letter in docs):
            _logger.info('letter has a5 paper')
            # data = {'docids': docids, 'employee_id': employee.id, 'now_date': now_date}
            # return self.env.ref('ubisol_letters.letter_detail_report_a5_pdf').report_action(self)

            # data = []
            # datas = {
            #     'docids': docids,
            #     'model': 'ubi.letter.going',
            #     'form': data
            # }
            # return {
            #     'type': 'ir.actions.report.xml',
            #     'report_name': 'report.ubisol_letters.letter_detail_report_a5',
            #     'datas': datas,
            # }
        else:    
            return {
                'now_date': now_date,
                'docs': docs,
                'employee': employee
            }