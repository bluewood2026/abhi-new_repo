# -*- coding: utf-8 -*-
###############################################################################
#
#    Auto Attendance Check-in/Check-out Module for Odoo 19
#
#    This file extends ir.http to track user activity on every request
#    so we can detect when browser is closed (no activity)
#
###############################################################################
import logging
from odoo import models
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    """ Extend ir.http to track user activity on every request."""
    _inherit = 'ir.http'

    def session_info(self):
        """ Override session_info to track user activity."""
        result = super(IrHttp, self).session_info()
        
        # Track user activity on every request
        try:
            if request and request.session and request.session.uid:
                # Check if model exists in registry
                if 'user.session.tracker' not in self.env.registry:
                    return result
                
                # Check if table exists
                try:
                    cr = self.env.cr
                    cr.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'user_session_tracker'
                        );
                    """)
                    table_exists = cr.fetchone()[0]
                    if not table_exists:
                        return result  # Table doesn't exist yet
                except Exception:
                    return result  # Can't check, skip
                
                user_id = request.session.uid
                session_id = request.session.session_token if hasattr(request.session, 'session_token') else None
                
                # Update user activity tracker
                try:
                    tracker_model = self.env['user.session.tracker']
                    tracker_model.update_user_activity(user_id, session_id)
                except Exception as table_error:
                    # Table might not exist yet, fail silently
                    _logger.debug("Session tracker not available: %s" % str(table_error))
        except Exception as e:
            # Don't break if tracking fails
            _logger.debug("Error tracking user activity: %s" % str(e))
        
        return result

    @classmethod
    def _authenticate(cls, session):
        """ Track user activity on authentication."""
        result = super(IrHttp, cls)._authenticate(session)
        
        # Track activity after authentication
        try:
            if session and session.uid:
                # Check if model exists in registry
                env = request.env(context=dict(request.context, sudo=True))
                if 'user.session.tracker' not in env.registry:
                    return result
                
                user_id = session.uid
                session_id = session.session_token if hasattr(session, 'session_token') else None
                
                # Update user activity tracker (handle table not existing gracefully)
                try:
                    tracker_model = env['user.session.tracker']
                    tracker_model.update_user_activity(user_id, session_id)
                except Exception as table_error:
                    # Table might not exist yet, fail silently
                    _logger.debug("Session tracker not available on auth: %s" % str(table_error))
        except Exception as e:
            _logger.debug("Error tracking user activity on auth: %s" % str(e))
        
        return result


