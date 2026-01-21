{
    'name': 'Survey Auto Next',
    'version': '1.0',
    'category': 'Survey',
    'author': 'Abdul Wahid',
    'website': 'https://linkedin.com/in/abdul-wahid-7aab6b240',
    'summary': 'Auto move to next survey page after timer expires',
    'description': 'Adds a countdown timer per survey page and automatically moves to next page when time is up.',
    'depends': ['survey'],
    'data': [

    ],
    'assets': {
        'web.assets_frontend': [
            'survey_auto_next/static/src/js/survey_auto_next.js',
        ],
    },
    'installable': True,
    'application': False,
}
