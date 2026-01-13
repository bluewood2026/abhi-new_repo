# -*- coding: utf-8 -*-
###############################################################################
#
#    Auto Attendance Check-in/Check-out Module for Odoo 19
#
#    This file handles automatic check-in when user logs in
#
###############################################################################
import logging
from datetime import datetime, timedelta
import pytz
from odoo import models, fields, _

_logger = logging.getLogger(__name__)


def get_australia_time():
    """Get current time in AEST (Australian Eastern Standard Time, UTC+10 fixed, no DST).
    Converts from UTC to AEST by adding 10 hours."""
    try:
        # Get current UTC time
        utc_now = datetime.utcnow()
        _logger.debug("🌏 [get_australia_time] Current UTC time: %s", utc_now)
        
        # AEST = UTC + 10 hours (fixed offset, no DST)
        aest_time = utc_now + timedelta(hours=10)
        _logger.info("🌏 [get_australia_time] UTC: %s -> AEST (UTC+10): %s", utc_now, aest_time)
        
        return aest_time
    except Exception as e:
        _logger.error("❌ [get_australia_time] Timezone conversion error: %s", str(e))
        _logger.exception("Full error traceback:")
        _logger.warning("⚠️ [get_australia_time] Falling back to server time")
        return datetime.now()


class ResUsers(models.Model):
    """ Inherits 'res.users' to add automatic attendance check-in on login."""
    _inherit = 'res.users'

    def _check_credentials(self, password, user_agent_env):
        """ Check user credentials during login and create attendance check-in."""
        _logger.info("🔐 [ResUsers._check_credentials] Function started - Checking credentials")
        
        try:
            result = super(ResUsers, self)._check_credentials(
                password, user_agent_env)
            _logger.info("✅ [ResUsers._check_credentials] Credentials validated successfully")
        except Exception as e:
            _logger.error("❌ [ResUsers._check_credentials] Credential validation failed: %s", str(e))
            raise
        
        # After successful authentication, get the user and create check-in
        # self can be a recordset with the user or empty, so we use env.user or browse by uid
        try:
            uid = self.env.uid
            _logger.info("👤 [ResUsers._check_credentials] User ID from env: %s", uid)
            
            if uid:
                # Create attendance check-in for the authenticated user
                user = self.env['res.users'].browse(uid)
                _logger.info("🔍 [ResUsers._check_credentials] Browsed user: %s (ID: %s)", user.name if user.exists() else 'N/A', uid)
                
                if user.exists():
                    _logger.info("🚀 [ResUsers._check_credentials] Calling _auto_checkin_attendance for user: %s", user.name)
                    user._auto_checkin_attendance()
                else:
                    _logger.warning("⚠️ [ResUsers._check_credentials] User with ID %s does not exist", uid)
            else:
                _logger.warning("⚠️ [ResUsers._check_credentials] No user ID found in env.uid")
        except Exception as e:
            # Log error but don't block login
            _logger.warning(
                "⚠️ [ResUsers._check_credentials] Could not create automatic check-in during login: %s", str(e))
        
        _logger.info("✅ [ResUsers._check_credentials] Function completed")
        return result

    def _auto_checkin_attendance(self):
        """ Automatically create attendance check-in for the logged-in user."""
        _logger.info("🚀 [ResUsers._auto_checkin_attendance] Function started for user: %s (ID: %s)", self.name, self.id)
        
        try:
            # Get the employee record linked to this user
            _logger.info("🔍 [ResUsers._auto_checkin_attendance] Searching for employee linked to user ID: %s", self.id)
            employee = self.env['hr.employee'].search([
                ('user_id', '=', self.id)
            ], limit=1)

            if not employee:
                _logger.info(
                    "⚠️ [ResUsers._auto_checkin_attendance] User %s has no linked employee record. "
                    "Skipping automatic attendance check-in.", self.name)
                return

            _logger.info("✅ [ResUsers._auto_checkin_attendance] Found employee: %s (ID: %s)", employee.name, employee.id)

            # Check if employee is already checked in today (without check_out)
            _logger.info("🔍 [ResUsers._auto_checkin_attendance] Checking for existing attendance for employee: %s", employee.name)
            attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1, order='check_in desc')

            if attendance:
                _logger.info(
                    "⚠️ [ResUsers._auto_checkin_attendance] Employee %s is already checked in (Attendance ID: %s). "
                    "Skipping duplicate check-in.", employee.name, attendance.id)
                # Update tracker with existing attendance
                _logger.info("📝 [ResUsers._auto_checkin_attendance] Updating session tracker with existing attendance")
                self._update_session_tracker(attendance.id)
                return

            # Create check-in attendance record
            # Use fields.Datetime.now() - Odoo automatically handles UTC storage and user timezone display
            check_in_time_str = fields.Datetime.now()
            check_in_time = fields.Datetime.from_string(check_in_time_str)  # Convert to datetime for calculations
            _logger.info("⏰ [ResUsers._auto_checkin_attendance] Check-in time: %s (stored as UTC, displayed in user timezone)", check_in_time_str)
            
            attendance_vals = {
                'employee_id': employee.id,
                'check_in': check_in_time_str,  # Store as string (Odoo format)
            }
            _logger.info("📋 [ResUsers._auto_checkin_attendance] Creating attendance with values: %s", attendance_vals)
            
            attendance = self.env['hr.attendance'].sudo().create(attendance_vals)
            _logger.info("✅ [ResUsers._auto_checkin_attendance] Attendance created successfully (ID: %s)", attendance.id)
            
            # Create/update session tracker
            _logger.info("📝 [ResUsers._auto_checkin_attendance] Updating session tracker")
            self._update_session_tracker(attendance.id)
            
            # Check for late arrival
            _logger.info("🔍 [ResUsers._auto_checkin_attendance] Checking for late arrival")
            calendar = employee.resource_calendar_id
            
            if calendar:
                _logger.info("📅 [ResUsers._auto_checkin_attendance] Found calendar: %s (ID: %s)", calendar.name, calendar.id)
                day_of_week = str(check_in_time.weekday())
                _logger.info("📆 [ResUsers._auto_checkin_attendance] Day of week: %s (0=Monday, 6=Sunday)", day_of_week)
                
                morning_line = calendar.attendance_ids.filtered(
                    lambda l: l.dayofweek == day_of_week and l.day_period == 'morning'
                )
                
                if morning_line:
                    # Get the first morning line if multiple exist
                    if len(morning_line) > 1:
                        _logger.info("⚠️ [ResUsers._auto_checkin_attendance] Multiple morning lines found (%s), using first one", len(morning_line))
                        morning_line = morning_line[0]
                    
                    _logger.info("🌅 [ResUsers._auto_checkin_attendance] Morning line found: %s (ID: %s)", 
                               morning_line.name if hasattr(morning_line, 'name') and morning_line.name else 'N/A', 
                               morning_line.id if hasattr(morning_line, 'id') else 'N/A')
                    _logger.info("⏰ [ResUsers._auto_checkin_attendance] Morning line hour_from: %s (type: %s)", 
                               morning_line.hour_from, type(morning_line.hour_from).__name__)
                    
                    # Convert hour_from (float) to hours and minutes
                    # In Odoo, hour_from is stored as float: 9.0 = 9:00, 9.5 = 9:30, 9.25 = 9:15
                    hour_from_float = float(morning_line.hour_from)
                    expected_hour = int(hour_from_float)
                    expected_minute = int(round((hour_from_float - expected_hour) * 60))
                    
                    # Ensure minute is between 0-59
                    if expected_minute >= 60:
                        expected_hour += 1
                        expected_minute = 0
                    
                    _logger.info("🕐 [ResUsers._auto_checkin_attendance] Parsed hour_from: %s -> Hour: %s, Minute: %s", 
                               hour_from_float, expected_hour, expected_minute)
                    
                    # Convert check_in_time (UTC) to AEST for comparison
                    # check_in_time is in UTC, we need to convert it to AEST first
                    try:
                        aest_tz = pytz.timezone('Australia/Brisbane')
                        # Convert UTC check_in_time to AEST
                        check_in_utc = pytz.UTC.localize(check_in_time)
                        check_in_aest = check_in_utc.astimezone(aest_tz)
                        check_in_aest_naive = check_in_aest.replace(tzinfo=None)
                        _logger.info("🔄 [ResUsers._auto_checkin_attendance] Check-in UTC: %s -> AEST: %s", check_in_time, check_in_aest_naive)
                    except Exception as tz_err:
                        _logger.warning("⚠️ [ResUsers._auto_checkin_attendance] Timezone conversion error, using UTC time: %s", str(tz_err))
                        # Fallback: assume UTC+10 if conversion fails
                        check_in_aest_naive = check_in_time + timedelta(hours=10)
                        _logger.info("🔄 [ResUsers._auto_checkin_attendance] Using fallback: UTC + 10 hours = %s", check_in_aest_naive)
                    
                    # Create expected datetime in AEST (local time)
                    # Expected time is 9:00 AM in AEST timezone
                    expected_dt_aest = check_in_aest_naive.replace(
                        hour=expected_hour,
                        minute=expected_minute,
                        second=0,
                        microsecond=0
                    )
                    _logger.info("🕐 [ResUsers._auto_checkin_attendance] Expected check-in time (AEST): %s", expected_dt_aest)
                    _logger.info("⏰ [ResUsers._auto_checkin_attendance] Actual check-in time (AEST): %s", check_in_aest_naive)

                    # Calculate delay in minutes (both times are in AEST now)
                    time_diff = check_in_aest_naive - expected_dt_aest
                    delay_minutes = time_diff.total_seconds() / 60.0
                    _logger.info("⏱️ [ResUsers._auto_checkin_attendance] Time difference: %s seconds = %.2f minutes", 
                               time_diff.total_seconds(), delay_minutes)

                    if delay_minutes > 15:
                        late_minutes = round(delay_minutes, 2)
                        _logger.warning(
                            "⚠️ [ResUsers._auto_checkin_attendance] Employee %s is LATE by %.2f minutes! (Expected: %s, Actual: %s)",
                            employee.name, late_minutes, expected_dt_aest, check_in_aest_naive
                        )

                        _logger.info("💾 [ResUsers._auto_checkin_attendance] Writing late_minutes: %.2f to attendance ID: %s", 
                                   late_minutes, attendance.id)
                        attendance.write({'late_minutes': late_minutes})
                        _logger.info("✅ [ResUsers._auto_checkin_attendance] late_minutes saved successfully")

                        _logger.info("📧 [ResUsers._auto_checkin_attendance] Creating activity for late arrival")
                        activity_type = self.env.ref('mail.mail_activity_data_todo')
                        _logger.info("📋 [ResUsers._auto_checkin_attendance] Activity type: %s", activity_type.name if activity_type else 'None')
                        
                        vals = {
                            'res_model_id': self.env['ir.model']._get_id('hr.employee'),
                            'res_id': employee.id,
                            'activity_type_id': activity_type.id,
                            'user_id': employee.user_id.id,
                            'summary': 'Late Arrival',
                            'note': f"You arrived late by **{late_minutes} minutes**.",
                            'date_deadline': fields.Date.today(),
                        }
                        _logger.info("📝 [ResUsers._auto_checkin_attendance] Creating activity with values: %s", vals)
                        activity = self.env['mail.activity'].sudo().create(vals)
                        _logger.info("✅ [ResUsers._auto_checkin_attendance] Activity created successfully (ID: %s)", activity.id)
                        
                        _logger.info("👥 [ResUsers._auto_checkin_attendance] Checking for manager notification group")
                        group = self.env.ref('auto_attendance_checkin.group_late_attendance_notify',
                                             raise_if_not_found=False)
                        if group:
                            _logger.info("✅ [ResUsers._auto_checkin_attendance] Found notification group: %s (Users: %s)", 
                                       group.name, len(group.user_ids))
                            for user in group.user_ids:
                                # avoid duplicate activity for the same user
                                if user.id == employee.user_id.id:
                                    _logger.info("⏭️ [ResUsers._auto_checkin_attendance] Skipping activity for employee user: %s", user.name)
                                    continue

                                _logger.info("📧 [ResUsers._auto_checkin_attendance] Creating manager notification for user: %s", user.name)
                                manager_vals = {
                                    'res_model_id': self.env['ir.model']._get_id('hr.employee'),
                                    'res_id': employee.id,
                                    'activity_type_id': activity_type.id,
                                    'user_id': user.id,
                                    'summary': _('Employee Late Arrival'),
                                    'note': _(
                                        "Employee %s arrived late by %s minutes."
                                    ) % (employee.name, late_minutes),
                                    'date_deadline': fields.Date.today(),
                                }
                                manager_activity = self.env['mail.activity'].sudo().create(manager_vals)
                                _logger.info("✅ [ResUsers._auto_checkin_attendance] Manager activity created (ID: %s) for user: %s", 
                                           manager_activity.id, user.name)
                        else:
                            _logger.info("⚠️ [ResUsers._auto_checkin_attendance] Notification group not found")
                    else:
                        _logger.info("✅ [ResUsers._auto_checkin_attendance] Employee %s arrived on time (delay: %.2f minutes, threshold: 15 minutes)", 
                                   employee.name, delay_minutes)
                else:
                    _logger.info("⚠️ [ResUsers._auto_checkin_attendance] No morning line found for day: %s", day_of_week)
            else:
                _logger.info("⚠️ [ResUsers._auto_checkin_attendance] No calendar found for employee: %s", employee.name)
            
            _logger.info("✅ [ResUsers._auto_checkin_attendance] Automatic check-in completed successfully for employee: %s", employee.name)
                
        except Exception as e:
            _logger.error(
                "❌ [ResUsers._auto_checkin_attendance] Error creating automatic check-in for user %s: %s", 
                self.name, str(e), exc_info=True)

    def _update_session_tracker(self, attendance_id=None):
        """ Create or update session tracker for user activity tracking."""
        _logger.info("📝 [ResUsers._update_session_tracker] Function started for user: %s (ID: %s) | Attendance ID: %s", 
                    self.name, self.id, attendance_id)
        
        # Skip tracker update if table doesn't exist (module not upgraded yet)
        try:
            _logger.info("🔍 [ResUsers._update_session_tracker] Checking if tracker model exists in registry")
            # Check if model exists in registry
            if 'user.session.tracker' not in self.env.registry:
                _logger.info("⚠️ [ResUsers._update_session_tracker] Tracker model not in registry, skipping")
                return
            
            _logger.info("✅ [ResUsers._update_session_tracker] Tracker model found in registry")
            
            # Check if table actually exists in database
            _logger.info("🔍 [ResUsers._update_session_tracker] Checking if tracker table exists in database")
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
                # Table doesn't exist yet, skip tracker update
                _logger.info("⚠️ [ResUsers._update_session_tracker] Tracker table doesn't exist yet, skipping")
                return
            
            _logger.info("✅ [ResUsers._update_session_tracker] Tracker table exists")
            
        except Exception as check_error:
            # If we can't check, skip tracker to avoid breaking login
            _logger.debug("⚠️ [ResUsers._update_session_tracker] Cannot check tracker table existence: %s", str(check_error))
            return
        
        # Now safely try to update/create tracker
        try:
            _logger.info("🔍 [ResUsers._update_session_tracker] Getting session ID from request")
            # Try to get session from request if available
            session_id = None
            try:
                from odoo.http import request
                if request and hasattr(request, 'session'):
                    session_id = getattr(request.session, 'session_token', None)
                    _logger.info("✅ [ResUsers._update_session_tracker] Session ID retrieved: %s", session_id)
                else:
                    _logger.info("⚠️ [ResUsers._update_session_tracker] Request or session not available")
            except Exception as req_error:
                _logger.debug("⚠️ [ResUsers._update_session_tracker] Could not get session from request: %s", str(req_error))
                pass
            
            # Update or create session tracker
            _logger.info("🔍 [ResUsers._update_session_tracker] Searching for existing tracker")
            tracker_model = self.env['user.session.tracker']
            
            # Use sudo to avoid access rights issues
            with self.env.cr.savepoint():
                tracker = tracker_model.sudo().search([
                    ('user_id', '=', self.id),
                    ('is_active', '=', True)
                ], limit=1)
                
                _logger.info("📋 [ResUsers._update_session_tracker] Existing tracker found: %s (ID: %s)", 
                           'Yes' if tracker else 'No', tracker.id if tracker else 'N/A')
                
                tracker_vals = {
                    'user_id': self.id,
                    'session_id': session_id or 'unknown',
                    'last_activity': datetime.now(),
                    'is_active': True,
                }
                
                if attendance_id:
                    tracker_vals['attendance_id'] = attendance_id
                    _logger.info("📝 [ResUsers._update_session_tracker] Adding attendance_id to tracker: %s", attendance_id)
                
                if tracker:
                    _logger.info("✏️ [ResUsers._update_session_tracker] Updating existing tracker (ID: %s) with values: %s", 
                               tracker.id, tracker_vals)
                    tracker.write(tracker_vals)
                    _logger.info("✅ [ResUsers._update_session_tracker] Tracker updated successfully")
                else:
                    tracker_vals['login_time'] = datetime.now()
                    _logger.info("➕ [ResUsers._update_session_tracker] Creating new tracker with values: %s", tracker_vals)
                    new_tracker = tracker_model.sudo().create(tracker_vals)
                    _logger.info("✅ [ResUsers._update_session_tracker] New tracker created successfully (ID: %s)", new_tracker.id)
                
        except Exception as e:
            # Fail silently - don't break login if tracker fails
            _logger.debug("⚠️ [ResUsers._update_session_tracker] Error updating session tracker: %s", str(e))
        
        _logger.info("✅ [ResUsers._update_session_tracker] Function completed")

