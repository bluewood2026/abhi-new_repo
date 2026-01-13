# -*- coding: utf-8 -*-
###############################################################################
#
#    Auto Attendance Check-in/Check-out Module for Odoo 19
#
#    This file handles automatic check-out when user logs out
#
###############################################################################
import logging
from datetime import datetime
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class AutoAttendanceController(http.Controller):
    """ Controller to handle automatic attendance check-out on logout."""

    def _create_checkout(self, user):
        """ Helper method to create check-out for a user."""
        try:
            if not user or not user.exists():
                return False
            
            # Deactivate session tracker (user is logging out)
            try:
                tracker_model = request.env['user.session.tracker']
                tracker_model.deactivate_session(user.id)
            except Exception as e:
                _logger.debug("Error deactivating session tracker: %s" % str(e))
                
            # Get the employee record linked to this user
            employee = request.env['hr.employee'].sudo().search([
                ('user_id', '=', user.id)
            ], limit=1)

            if not employee:
                _logger.info(
                    "User %s has no linked employee record. "
                    "Skipping automatic attendance check-out." % user.name)
                return False

            # Find the latest check-in without check-out
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1, order='check_in desc')

            if attendance:
                # Create check-out for the attendance record
                attendance.write({
                    'check_out': datetime.now()
                })
                _logger.info(
                    "Automatic check-out created for employee: %s" % 
                    employee.name)
                return True
            else:
                _logger.info(
                    "No active check-in found for employee %s. "
                    "Skipping check-out." % employee.name)
                return False
                
        except Exception as e:
            _logger.error(
                "Error creating automatic check-out for user %s: %s" % 
                (user.name if user and user.exists() else 'Unknown', str(e)))
            return False

    @http.route('/web/session/logout', type='http', auth="user", methods=['GET', 'POST'], csrf=False)
    def logout_http(self, redirect='/web'):
        """ Override HTTP logout route to create attendance check-out."""
        user = request.env.user
        self._create_checkout(user)
        
        # Call the original logout using session manager
        request.session.logout(keep_db=True)
        return request.redirect('/web/login?redirect=%s' % redirect, 303)

    @http.route('/web/session/destroy', type='json', auth="user")
    def logout_json(self):
        """ Override JSON logout route to create attendance check-out."""
        user = request.env.user
        self._create_checkout(user)
        
        # Call the original logout
        request.session.logout(keep_db=True)
        return {'url': '/web/login'}

