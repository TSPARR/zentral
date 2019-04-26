from django.conf.urls import url

from . import views

app_name = "incidents"
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>\d+)/$', views.IncidentView.as_view(), name='incident'),
    url(r'^(?P<pk>\d+)/events/$', views.IncidentEventsView.as_view(), name='incident_events'),
]

main_menu_cfg = {
    'weight': 2,
    'items': (
        ('index', 'all incidents'),
    ),
}
