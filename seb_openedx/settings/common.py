"""
Settings for seb_openedx
"""

from __future__ import absolute_import, unicode_literals


SECRET_KEY = 'a-not-to-be-trusted-secret-key'
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'seb_openedx',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


def plugin_settings(settings):
    """
    Defines seb_openedx settings when app is used as a plugin to edx-platform.
    See: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """
    settings.SEB_COURSE_MODULE = 'seb_openedx.edxapp_wrapper.backends.get_course_module_h_v1'
    settings.SEB_COURSEWARE_MODULE = 'seb_openedx.edxapp_wrapper.backends.get_courseware_module_h_v1'
    settings.SEB_GET_CHAPTER_FROM_LOCATION = 'seb_openedx.edxapp_wrapper.backends.get_chapter_from_location_h_v1'
    settings.SEB_CONFIGURATION_HELPERS = 'seb_openedx.edxapp_wrapper.backends.get_configuration_helpers_h_v1'
    settings.SEB_EDXMAKO_MODULE = 'seb_openedx.edxapp_wrapper.backends.edxmako_module_h_v1'
    settings.SEB_PERMISSION_COMPONENTS = ['AlwaysAllowStaff', 'CheckSEBKeysRequestHash']
    settings.SEB_KEY_SOURCES = ['from_global_settings', 'from_other_course_settings', 'from_site_configuration']

    # When SEB determines the access is denied one may specify what to whitelist/blacklist more granularly
    settings.SEB_WHITELIST_PATHS = []
    settings.SEB_BLACKLIST_CHAPTERS = []
    settings.SEB_USER_BANNING_BACKEND = 'DatabaseBannedUsersBackend'  # can also be 'UserprofileBannedUsersBackend' (not yet implemented)
    settings.SEB_USER_BANNING_ENABLED = True
