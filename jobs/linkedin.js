//!> schedule: */5 * * * *

(function() {
  'use strict';
  var state = webbingo_control.get_state;
  if (state === 'main') {
    webbingo_control.load('https://www.linkedin.com/company/1038', 'company_page');
    webbingo_control.log_message('Raised Load Request');
    webbingo_control.done()
  } else if (state === 'company_page') {
    webbingo_control.log_message('In Company Page State');

    var page_count = 1;

    var target = $("#feed-show-more")[0];
    var observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        console.log('Type' + mutation.type);
        if(!$(mutation.target).hasClass('disabled')) {
          console.log('Triggering Click!');
          $('.view-more').trigger('click');
          page_count = page_count + 1;
          if(page_count > 20) {
            observer.disconnect();
          }
        }
      });
    });
    var config = {
      attributes: true,
      childList: false,
      characterData: false
    };
    observer.observe(target, config);
    console.log('Triggering Click!');
    $('.view-more').trigger('click');

    // Later, you can stop observing
    //observer.disconnect();
  }
}).call(this);

