from collections import namedtuple


class Job(namedtuple('Job', ['file',
                             'schedule',
                             'state',
                             'url',
                             'block_images',
                             'proxy_only_html',
                             'proxy',
                             'proxy_auth',
                             'filter_list',
                             'is_crawlera',
                             'meta_data',
                             'retry',
                             'timeout'])):
    def __new__(cls, **args):
        if not args:
            raise Exception('Empty job request')
        if 'retry' not in args:
            args['retry'] = 1
        return super(Job, cls).__new__(cls, **{x: args.get(x) for x in Job._fields})

    def new_state(self, **args):
        args['file'] = self.file
        args['schedule'] = self.schedule
        return Job(**args)

    def get_retry_job(self):
        d = self.dict()
        d['retry'] += 1
        return Job(**d)

    def dict(self):
        return {x: getattr(self, x) for x in Job._fields}