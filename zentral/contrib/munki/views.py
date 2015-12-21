import logging
from datetime import timedelta
from dateutil import parser
from django.utils import timezone
from zentral.utils.api_views import SignedRequestHeaderJSONPostAPIView
from .events import post_munki_events
from .models import MunkiState

logger = logging.getLogger('zentral.contrib.munki.views')


class BaseView(SignedRequestHeaderJSONPostAPIView):
    verify_module = "zentral.contrib.munki"


class JobDetailsView(BaseView):
    max_binaryinfo_age = timedelta(hours=1)

    def get(self, request, *args, **kwargs):
        msn = kwargs['machine_serial_number']
        response_d = {'include_santa_binaryinfo': True}
        try:
            munki_state = MunkiState.objects.get(machine_serial_number=msn)
        except MunkiState.DoesNotExist:
            pass
        else:
            response_d['last_seen_sha1sum'] = munki_state.sha1sum
            if munki_state.binaryinfo_last_seen:
                last_binaryinfo_age = timezone.now() - munki_state.binaryinfo_last_seen
                response_d['include_santa_binaryinfo'] = last_binaryinfo_age >= self.max_binaryinfo_age
        return response_d


class PostJobView(BaseView):
    def post(self, request, *args, **kwargs):
        msn = self.data['machine']['serial_number']
        reports = [(parser.parse(r.pop('start_time')),
                    parser.parse(r.pop('end_time')),
                    r) for r in self.data.pop('reports')]
        # Events
        post_munki_events(msn,
                          self.user_agent,
                          self.ip,
                          (r for _, _, r in reports))
        # MunkiState
        update_dict = {'user_agent': self.user_agent,
                       'ip': self.ip}
        if self.data.get('santa_binaryinfo_included', False):
            update_dict['binaryinfo_last_seen'] = timezone.now()
        if reports:
            reports.sort()
            start_time, end_time, report = reports[-1]
            update_dict.update({'munki_version': report.get('munki_version', None),
                                'sha1sum': report['sha1sum'],
                                'run_type': report['run_type'],
                                'start_time': start_time,
                                'end_time': end_time})
        MunkiState.objects.update_or_create(machine_serial_number=msn,
                                            defaults=update_dict)
        return {}
