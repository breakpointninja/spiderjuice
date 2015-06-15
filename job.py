from collections import namedtuple


class Job(namedtuple('Job', ['file', 'schedule', 'state', 'url', 'proxy_only_html', 'proxy', 'filter_list'])):
    def __new__(cls, **args):
        if not args:
            raise Exception('Empty job request')
        return super(Job, cls).__new__(cls, **{x: args.get(x) for x in Job._fields})

    def new_state(self, **args):
        args['file'] = self.file
        args['schedule'] = self.schedule
        return Job(**args)