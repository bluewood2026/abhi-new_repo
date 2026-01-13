# -*- coding: utf-8 -*-
###############################################################################
#
#    Auto Attendance Check-in/Check-out Module for Odoo 19
#
#    This file tracks user sessions to detect browser close and create check-out
#
###############################################################################
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class UserSessionTracker(models.Model):
    """ Track user sessions and last activity to detect browser close."""
    _name = 'user.session.tracker'
    _description = 'User Session Activity Tracker'
    _order = 'last_activity desc'

    user_id = fields.Many2one('res.users', string='User', required=True, index=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', related='user_id.employee_id', store=False, readonly=True)
    session_id = fields.Char(string='Session ID', index=True)
    last_activity = fields.Datetime(string='Last Activity', required=True, index=True, default=fields.Datetime.now)
    login_time = fields.Datetime(string='Login Time', required=True, default=fields.Datetime.now)
    is_active = fields.Boolean(string='Is Active', default=True, index=True)
    attendance_id = fields.Many2one('hr.attendance', string='Current Attendance', ondelete='set null')
    
    # Note: SQL constraints removed - Odoo 19 uses model.Constraint instead
    # Fields already have required=True which enforces constraints at ORM level

    @api.model
    def update_user_activity(self, user_id, session_id=None):
        """ Update user's last activity timestamp."""
        try:
            # First check if table exists
            cr = self.env.cr
            try:
                cr.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'user_session_tracker'
                    );
                """)
                table_exists = cr.fetchone()[0]
                if not table_exists:
                    return  # Table doesn't exist yet, skip
            except Exception:
                # Can't check table, skip to avoid breaking
                return
            
            # Find or create tracker for this user
            domain = [
                ('user_id', '=', user_id),
                ('is_active', '=', True)
            ]
            if session_id:
                domain.append(('session_id', '=', session_id))
            
            # Use savepoint to avoid transaction abort
            with self.env.cr.savepoint():
                tracker = self.sudo().search(domain, limit=1)
                
                if tracker:
                    tracker.write({
                        'last_activity': fields.Datetime.now(),
                    })
                else:
                    # Create new tracker if not exists
                    self.sudo().create({
                        'user_id': user_id,
                        'session_id': session_id or 'unknown',
                        'last_activity': fields.Datetime.now(),
                        'login_time': fields.Datetime.now(),
                        'is_active': True,
                    })
        except Exception as e:
            # Fail silently - don't break if tracking fails
            _logger.debug("Error updating user activity for user %s: %s" % (user_id, str(e)))

    @api.model
    def deactivate_session(self, user_id):
        """ Mark session as inactive (called on logout)."""
        try:
            trackers = self.search([
                ('user_id', '=', user_id),
                ('is_active', '=', True)
            ])
            trackers.write({'is_active': False})
        except Exception as e:
            _logger.error("Error deactivating session for user %s: %s" % (user_id, str(e)))

    @api.model
    def check_inactive_sessions_and_checkout(self):
        """ Cron job: Check for inactive sessions and create check-out."""
        try:
            # Inactivity threshold: 15 minutes (no activity)
            inactivity_threshold = datetime.now() - timedelta(minutes=15)
            
            # Find active trackers with no recent activity
            inactive_trackers = self.search([
                ('is_active', '=', True),
                ('last_activity', '<', inactivity_threshold),
            ])
            
            checkout_count = 0
            
            for tracker in inactive_trackers:
                try:
                    user = tracker.user_id
                    if not user or not user.exists():
                        continue
                    
                    # Skip system users
                    if user.id in [1, 2]:
                        tracker.write({'is_active': False})
                        continue
                    
                    # Get employee
                    employee = self.env['hr.employee'].search([
                        ('user_id', '=', user.id),
                        ('active', '=', True)
                    ], limit=1)
                    
                    if not employee:
                        tracker.write({'is_active': False})
                        continue
                    
                    # Find attendance without check-out
                    attendance = self.env['hr.attendance'].search([
                        ('employee_id', '=', employee.id),
                        ('check_out', '=', False)
                    ], limit=1, order='check_in desc')
                    
                    if attendance:
                        # Create check-out (use last activity or reasonable time)
                        check_out_time = tracker.last_activity
                        
                        # Calculate work duration
                        check_in_time = attendance.check_in
                        check_in_dt = check_in_time.replace(tzinfo=None) if check_in_time.tzinfo else check_in_time
                        work_duration = (check_out_time - check_in_dt).total_seconds() / 3600
                        
                        # If more than 12 hours, set reasonable check-out
                        if work_duration > 12:
                            check_out_time = check_in_dt + timedelta(hours=8, minutes=30)
                        
                        attendance.sudo().write({
                            'check_out': check_out_time
                        })
                        
                        # Link attendance to tracker
                        tracker.write({
                            'attendance_id': attendance.id,
                            'is_active': False
                        })
                        
                        checkout_count += 1
                        _logger.info(
                            "Auto check-out created for inactive session: %s "
                            "(Last activity: %s, Check-in: %s, Check-out: %s)" %
                            (employee.name, tracker.last_activity.strftime('%H:%M:%S'),
                             check_in_time.strftime('%H:%M:%S'), check_out_time.strftime('%H:%M:%S')))
                    else:
                        # No attendance found, just deactivate tracker
                        tracker.write({'is_active': False})
                        
                except Exception as e:
                    _logger.error("Error processing inactive tracker %d: %s" % (tracker.id, str(e)))
                    # Deactivate tracker on error
                    tracker.write({'is_active': False})
            
            if checkout_count > 0:
                _logger.info("Auto check-out completed: %d check-outs created for inactive sessions" % checkout_count)
            
            return checkout_count
            
        except Exception as e:
            _logger.error("Error in check_inactive_sessions_and_checkout: %s" % str(e))
            return 0

    @api.model
    def cleanup_old_trackers(self):
        """ Cleanup old inactive trackers (older than 1 day)."""
        try:
            old_date = datetime.now() - timedelta(days=1)
            old_trackers = self.search([
                ('is_active', '=', False),
                ('last_activity', '<', old_date)
            ])
            if old_trackers:
                count = len(old_trackers)
                old_trackers.unlink()
                _logger.info("Cleaned up %d old session trackers" % count)
        except Exception as e:
            _logger.error("Error cleaning up old trackers: %s" % str(e))


