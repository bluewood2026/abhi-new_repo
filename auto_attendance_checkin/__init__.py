# -*- coding: utf-8 -*-
from . import models
from . import controllers

def post_init_hook(env):
    """ Hook called after module installation/upgrade."""
    from .models.cron_setup import post_init_hook as setup_crons
    setup_crons(env)

