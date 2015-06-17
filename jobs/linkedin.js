//!> schedule: once

(function () {
    'use strict';

    SjCtrl.onState('main', function (job) {
        SjCtrl.getJson('http://sites.contify.com/social_peek/api/getlinkedindata/', function (data) {
            var result = data.result, id;
            for (id in result) {
                var company_req = result[id];
                SjCtrl.log_message(company_req);
                SjCtrl.load({
                    url: 'https://www.linkedin.com/company/' + company_req.linkedin_company,
                    state: 'company_page',
                    filter_list: [
                        'allow:www\\.linkedin\\.com',
                        'allow:static\\.licdn\\.com',
                        'reject:.*'
                    ],
                    block_images: true,
          meta_data: company_req,
          proxy: 'paygo.crawlera.com:8010',
                    proxy_auth: 'contify:rXvX7FYcvs',
          is_crawlera: true
                });
            }
            SjCtrl.done();
        }, function (error_id) {
            console.log('Failed ' + error_id);
            SjCtrl.done();
        }, function () {
            console.log('Always');
        });

        /*SjCtrl.load({
         url: 'https://www.linkedin.com/company/deloitte',
         state: 'company_page',
         meta_data: {last_access_id: '321321321'},
         proxy: 'paygo.crawlera.com:8010',
         proxy_auth: 'contify:rXvX7FYcvs',
         block_images: true
         });
         SjCtrl.done();*/

    }).onState('company_page', function (job) {
        SjCtrl.log_message(job);
        var page_count = 1,
            max_page_count = 10,
            done = false,
            last_access_id = '',
            feed = $("#feed-show-more"),
            view_more = $('.view-more');

        if (job.meta_data.hasOwnProperty('last_access_id')) {
            last_access_id = job.meta_data.last_access_id;
            if (last_access_id.substr(0, 1) === 's') {
                last_access_id = last_access_id.substr(1);
            }
        }

        SjCtrl.log_message('last_access_id=' + last_access_id);

        function parseAndSubmit() {
            var result_list = [];
            $('.feed-item').each(function (index, element) {
                var title_element = $(element).find('.share-title .title'),
                    urls = [];

                if (title_element) {
                    var main_url = SjCtrl.relativeToAbsolute(title_element.attr('href'));
                    if (main_url) {
                        urls.push(main_url);
                    }
                }

                $(element).find('.share-body a').each(function (index, element) {
                    var url = SjCtrl.relativeToAbsolute($(element).attr('href'));
                    if (url) {
                        urls.push(url);
                    }
                });

                var result = {
                    id: $(element).attr('data-li-update-id'),
                    title: title_element.text(),
                    urls: urls,
                    share_url: SjCtrl.relativeToAbsolute($(element).find('.feed-item-meta > a').attr('href')),
                    pub_date: $(element).find('.feed-item-meta .nus-timestamp').text()
                };
                result_list.push(result);
            });

            if (result_list.length !== 0) {
                SjCtrl.post_obj("http://sites.contify.com/social_peek/api/addlinkedindata/", {"data": result_list, "search_keyword_id": job.meta_data.search_keyword_id});
            }

            done = true;
        }

        function isLastAccessIdPresent() {
            if (last_access_id === '') {
                return false;
            }
            var last_ac = $('li[data-li-update-id=' + last_access_id + ']'),
                is_present = last_ac.length !== 0;

            if (is_present) {
                SjCtrl.log_message('Found ID!! ' + last_access_id)
            }

            return is_present;
        }

        if (isLastAccessIdPresent() || feed.length === 0 || view_more.length === 0) {
            parseAndSubmit();
            SjCtrl.done();
            return;
        } else {
            var observer = new MutationObserver(function (mutations) {
                if (done) {
                    return;
                }
                mutations.forEach(function (mutation) {
                    if (done) {
                        return;
                    }
                    if (!$(mutation.target).hasClass('disabled')) {
                        SjCtrl.log_message('triggering click');
                        $('.view-more').trigger('click');
                        page_count = page_count + 1;
                        if (page_count > max_page_count || isLastAccessIdPresent() || feed.hasClass('done')) {
                            SjCtrl.log_message('Pages loaded');
                            observer.disconnect();
                            parseAndSubmit();
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

            observer.observe(feed[0], config);
            view_more.trigger('click');
        }
    }).run();
}).call(this);

