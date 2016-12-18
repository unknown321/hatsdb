from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import re
from dajaxice.core import dajaxice_autodiscover, dajaxice_config
dajaxice_autodiscover()


# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()



urlpatterns = patterns('',
    # Examples:
	# url(r'^admin/', include(admin.site.urls)),
#--------------------------------------------------------------------


# static
	url(r'^$', 'mongobase.views.index'),
	url(r'^buy/$', 'mongobase.views.buy'),
	url(r'^stats/$', 'mongobase.views.stats'),
	url(r'^faq/$', 'mongobase.views.faq'),
	url(r'^.html', 'mongobase.views.google'),

# login-logout
	url(r'^openid/', include('django_openid_auth.urls')),
	url(r'^logout/', 'mongobase.views.logout'),

# scanner
	url(r'^(?P<game_type>\w+)/scanner/$', 'mongobase.views.scanner'),
	url(r'^s/$', RedirectView.as_view(url='tf2/scanner/')),
	url(r'^scanner/$', 'mongobase.views.scanner'),
	url(r'^(?P<game_type>\w+)/friends/$', 'mongobase.views.scan_friends'),

# item-related pages
	url(r'^(?P<game_type>\w+)/unusuals/$', 'mongobase.views.unusuals'),
	url(r'^(?P<game_type>\w+)/tournament/$', 'mongobase.views.tournament'),

# tf2-specific pages
	url(r'^australium/$', 'mongobase.views.australium'),

# dota2-specific pages



# search
	url(r'^(?P<game_type>\w+)/search/$', 'mongobase.views.search'),
	# url(r'^(?P<game_type>\w+)/default_items/$', RedirectView.as_view(url='/%(game_type)s/search/')),
	# url(r'^(?P<game_type>\w+)/default_items/(?P<itemID>\w+)$', RedirectView.as_view(url='/%(game_type)s/search/')),

	# url(r'^(?P<game_type>\w+)/items/$', RedirectView.as_view(url='/%(game_type)s/search/')),
	# url(r'^(?P<game_type>\w+)/items/(?P<itemID>\w+)$', RedirectView.as_view(url='/%(game_type)s/search/')),

	
	# url(r'^(?P<game_type>\w+)/search/results$', 'mongobase.views.search_results'),

	url(r'^blacklist/$', 'mongobase.views.blacklist'),

#other 


	url(r'^admin_v2$', 'mongobase.views.admin_v2'),

	# url(r'^new_items/$', 'mongobase.views.show_new_items'),
	# url(r'^TEMP_new_items/$', 'mongobase.views.TEMP_new_items'),
	# url(r'^(?P<game_type>\w+)/blacklist/$', 'mongobase.views.blacklist_builder'),
	
	# url(r'^testpage/$', 'mongobase.views.test_view'),
	# url(r'^testpage2/$', 'mongobase.views.test_view2'),

	# url(r'^123/$', 'direct_to_template', {'template': 'connection.html'}),

#---------------ajax----------
	url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
)

urlpatterns += staticfiles_urlpatterns()
