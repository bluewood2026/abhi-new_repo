odoo.define('survey_auto_next.survey_auto_next', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.SurveyAutoNext = publicWidget.Widget.extend({
        selector: '.o_survey_form',
        start: function () {
            this._super.apply(this, arguments);
            this.initTimer();
        },

        initTimer: function () {
            const self = this;
            let seconds = 10; // set seconds per page

            let timerEl = $('<div/>', {
                class: 'auto-next-timer',
                css: {
                    'font-size': '18px',
                    'font-weight': 'bold',
                    'margin-bottom': '10px'
                }
            });
            this.$el.prepend(timerEl);

            function tick() {
                timerEl.text('Time left: ' + seconds + 's');
                if (seconds <= 0) {
                    let nextBtn = self.$el.find('button.o_survey_navigation_next');
                    if (nextBtn.length) {
                        nextBtn.click();
                    }
                } else {
                    seconds--;
                    setTimeout(tick, 1000);
                }
            }
            tick();
        }
    });
});
