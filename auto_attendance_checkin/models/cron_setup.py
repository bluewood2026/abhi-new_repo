# -*- coding: utf-8 -*-
###############################################################################
#
#    Auto Attendance Check-in/Check-out Module for Odoo 19
#
#    This file creates cron jobs programmatically
#
###############################################################################
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """ Create cron jobs after module installation."""
    try:
        # Find the model for user.session.tracker
        model = env['ir.model'].search([
            ('model', '=', 'user.session.tracker')
        ], limit=1)
        
        if not model:
            _logger.warning("user.session.tracker model not found, skipping cron creation")
            return
        
        # Find root user
        root_user = env.ref('base.user_root', raise_if_not_found=False)
        if not root_user:
            _logger.warning("Root user not found, skipping cron creation")
            return
        
        # Create cron job for checking inactive sessions
        cron_check = env['ir.cron'].search([
            ('name', '=', 'Auto Attendance: Check Inactive Sessions & Create Check-out')
        ], limit=1)
        
        if not cron_check:
            env['ir.cron'].create({
                'name': 'Auto Attendance: Check Inactive Sessions & Create Check-out',
                'model_id': model.id,
                'state': 'code',
                'code': 'model.check_inactive_sessions_and_checkout()',
                'interval_number': 5,
                'interval_type': 'minutes',
                'numbercall': -1,
                'active': True,
                'doall': False,
                'user_id': root_user.id,
            })
            _logger.info("Created cron job: Check Inactive Sessions & Create Check-out")
        else:
            # Update existing cron
            cron_check.write({
                'model_id': model.id,
                'code': 'model.check_inactive_sessions_and_checkout()',
                'interval_number': 5,
                'interval_type': 'minutes',
                'active': True,
            })
            _logger.info("Updated cron job: Check Inactive Sessions & Create Check-out")
        
        # Create cron job for cleanup
        cron_cleanup = env['ir.cron'].search([
            ('name', '=', 'Auto Attendance: Cleanup Old Session Trackers')
        ], limit=1)
        
        if not cron_cleanup:
            env['ir.cron'].create({
                'name': 'Auto Attendance: Cleanup Old Session Trackers',
                'model_id': model.id,
                'state': 'code',
                'code': 'model.cleanup_old_trackers()',
                'interval_number': 1,
                'interval_type': 'days',
                'numbercall': -1,
                'active': True,
                'doall': False,
                'user_id': root_user.id,
            })
            _logger.info("Created cron job: Cleanup Old Session Trackers")
        else:
            # Update existing cron
            cron_cleanup.write({
                'model_id': model.id,
                'code': 'model.cleanup_old_trackers()',
                'interval_number': 1,
                'interval_type': 'days',
                'active': True,
            })
            _logger.info("Updated cron job: Cleanup Old Session Trackers")
            
    except Exception as e:
        _logger.error("Error creating cron jobs in post_init_hook: %s" % str(e))

