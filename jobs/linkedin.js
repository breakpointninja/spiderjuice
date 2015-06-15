//!> schedule: */5 * * * *

(function() {
  'use strict';

  SjCtrl.onState('main', function() {
    SjCtrl.load({
      url: 'https://www.linkedin.com/company/1038',
      state: 'company_page',
      block_regex_list: ['^.*\.png$']
    });
    SjCtrl.log_message('Raised Load Request');
    SjCtrl.log_message('Log from SjCtrl');
    SjCtrl.done();
  }).onState('company_page', function() {
    SjCtrl.log_message('In Company Page State');

    var page_count = 1;

    var target = $("#feed-show-more")[0];
    var observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        console.log('Type' + mutation.type);
        if(!$(mutation.target).hasClass('disabled')) {
          console.log('Triggering Click!');
          $('.view-more').trigger('click');
          page_count = page_count + 1;
          if(page_count > 5) {
            observer.disconnect();
            SjCtrl.done();
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
  }).run();
}).call(this);

