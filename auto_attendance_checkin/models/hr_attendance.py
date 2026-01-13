import logging
from datetime import datetime
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    late_minutes = fields.Float(
        string="Late Minutes",
        digits=(16, 2),
        store=True,
        help="Number of minutes the employee was late"
    )

    @api.onchange('check_in')
    def _onchange_check_in(self):
        """Handle onchange event for check_in field."""
        _logger.info("🔔 [HrAttendance._onchange_check_in] Function started - Onchange triggered for check_in")

        try:
            if self.check_in:
                _logger.info(
                    "📋 [HrAttendance._onchange_check_in] Employee ID: %s | Check-in time: %s",
                    self.employee_id.id if self.employee_id else 'N/A',
                    self.check_in
                )

                if self.check_in.hour < 9:
                    _logger.warning(
                        "⏰ [HrAttendance._onchange_check_in] Early check-in detected | Time: %s | Hour: %s",
                        self.check_in,
                        self.check_in.hour
                    )
                    return {
                        'warning': {
                            'title': "Early Check In",
                            'message': "Office time 9 baje se start hota hai."
                        }
                    }
                else:
                    _logger.info(
                        "✅ [HrAttendance._onchange_check_in] Check-in time is valid | Time: %s",
                        self.check_in
                    )
            else:
                _logger.debug("⚠️ [HrAttendance._onchange_check_in] check_in is empty")
        except Exception as e:
            _logger.error(
                "❌ [HrAttendance._onchange_check_in] Error in onchange: %s",
                str(e)
            )
        
        _logger.info("✅ [HrAttendance._onchange_check_in] Function completed successfully")

