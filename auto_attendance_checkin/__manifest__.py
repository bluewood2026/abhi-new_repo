# -*- coding: utf-8 -*-
{
    'name': 'Auto Attendance Check-in/Check-out',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Automatically create attendance check-in on login and check-out on logout',
    'description': """
Auto Attendance Check-in/Check-out Module
=========================================
This module automatically creates attendance records:

* Check-in: When user logs into Odoo
* Check-out: When user logs out from Odoo OR browser is closed

Features:
---------
* Automatically links attendance to employee based on logged-in user
* Handles check-in on login
* Handles check-out on logout
* **Browser Close Detection**: Creates check-out even if browser is closed directly
* Session activity tracking to detect inactive users
* Automatic check-out for inactive sessions (15+ minutes no activity)
* Only creates attendance if user has linked employee record
* Prevents duplicate check-ins if already checked in

Requirements:
-------------
* Module 'hr_attendance' must be installed
* Users must have an employee record linked to their user account

How It Works:
-------------
1. On Login: Automatically creates check-in record
2. During Use: Tracks user activity on every request
3. On Logout: Creates check-out record immediately
4. On Browser Close: Cron job detects inactive sessions (15+ min no activity) and creates check-out automatically

Technical Details:
------------------
* Uses session tracking model to monitor user activity
* Cron job runs every 5 minutes to check for inactive sessions
* Automatically creates check-out if no activity for 15+ minutes
    """,
     'author': 'AM Odoo Solutions',
    'website': 'https://www.linkedin.com/in/ahmad-odoo5/',
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'security/group.xml',
        'views/attendance_views.xml',
        'views/hr_attendance_view.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
