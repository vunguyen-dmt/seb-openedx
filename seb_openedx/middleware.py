""" Middleware for seb_openedx """

import sys
import inspect
from django.http import HttpResponseNotFound
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment
from seb_openedx.edxapp_wrapper.edxmako_module import render_to_response, render_to_string
from seb_openedx.edxapp_wrapper.get_courseware_module import get_courseware_module
from seb_openedx.permissions import get_enabled_permission_classes
from seb_openedx.seb_courseware_index import SebCoursewareIndex
from seb_openedx.edxapp_wrapper.get_chapter_from_location import get_chapter_from_location
from seb_openedx.user_banning import is_user_banned, ban_user

SEB_WHITELIST_PATHS = getattr(settings, 'SEB_WHITELIST_PATHS', [])
SEB_BLACKLIST_CHAPTERS = getattr(settings, 'SEB_BLACKLIST_CHAPTERS', [])
BANNING_ENABLED = getattr(settings, 'SEB_USER_BANNING_ENABLED', True)


class SecureExamBrowserMiddleware(MiddlewareMixin):
    """ Middleware for seb_openedx """

    def __init__(self, get_response=None):
        """ declaring instance properties """
        super(SecureExamBrowserMiddleware, self).__init__(get_response)
        self.banned = False

    def process_view(self, request, view_func, view_args, view_kwargs):
        """ Start point of to d4etermine cms or lms """
        course_key_string = view_kwargs.get('course_key_string') or view_kwargs.get('course_id')
        course_key = CourseKey.from_string(course_key_string) if course_key_string else None

        if course_key:
            # By default is all denied
            access_denied = True

            if self.is_whitelisted_view(request, course_key):
                # First: Broad white-listing
                access_denied = False

            if self.is_blacklisted_chapter(request, course_key):
                # Second: Granular white-listing
                access_denied = True

            self.banned = False
            user_name = request.user.username if hasattr(request, 'user') else None

            active_comps = get_enabled_permission_classes()
            for permission in active_comps:
                if permission().check(request, course_key):
                    access_denied = False

            if BANNING_ENABLED and user_name and is_user_banned(user_name, course_key):
                self.banned = True
                access_denied = True

            if access_denied:
                return self.handle_access_denied(request, view_func, view_args, view_kwargs, course_key, user_name)

        return None

    # pylint: disable=too-many-arguments
    def handle_access_denied(self, request, view_func, view_args, view_kwargs, course_key, user_name):
        """ handle what to return and do when access denied """
        if BANNING_ENABLED and user_name and not self.banned:
            ban_user(user_name, course_key, '')
        courseware = get_courseware_module()
        is_courseware_view = bool(view_func.__name__ == courseware.views.index.CoursewareIndex.__name__)
        context = {"banned": self.banned}
        if is_courseware_view:
            return self.courseware_error_response(context, request, *view_args, **view_kwargs)
        return self.generic_error_response(context, request, course_key)

    def is_whitelisted_view(self, request, course_key):
        """ First broad filter: whitelisting of paths/tabs """

        # Whitelisting logic by alias
        aliases = {
            'discussion.views': 'discussion',
            'course_wiki.views': 'wiki',
            'openedx.features.course_experience': 'course-outline',
        }

        views_module = inspect.getmodule(request.resolver_match.func).__name__
        paths_matched = [aliases[key] for key in aliases if views_module.startswith(key)]
        alias_current_path = paths_matched[0] if paths_matched else None

        if alias_current_path in SEB_WHITELIST_PATHS:
            return True

        # Whitelisting xblocks when courseware
        if 'courseware' in SEB_WHITELIST_PATHS and self.is_xblock_request(request):
            return True

        # Whitelisting by url name
        if request.resolver_match.url_name:
            url_names_allowed = list(SEB_WHITELIST_PATHS) + ['jump_to', 'jump_to_id']
            for url_name in url_names_allowed:
                if request.resolver_match.url_name.startswith(url_name):
                    return True

        return False

    def is_blacklisted_chapter(self, request, course_key):
        """ Second more granular filter: blacklisting of specific chapters """
        chapter = request.resolver_match.kwargs.get('chapter')

        if not SEB_BLACKLIST_CHAPTERS:
            return False

        if chapter in SEB_BLACKLIST_CHAPTERS:
            return True

        if 'courseware' in SEB_WHITELIST_PATHS and self.is_xblock_request(request):
            usage_id = request.resolver_match.kwargs.get('usage_id')
            if usage_id:
                chapter = get_chapter_from_location(usage_id, course_key)
                if chapter in SEB_BLACKLIST_CHAPTERS:
                    return True
        return False

    def courseware_error_response(self, context, request, *view_args, **view_kwargs):
        """ error response when a chapter is being blocked """
        html = Fragment()
        html.add_content(render_to_string('seb-403-error-message.html', context))
        SebCoursewareIndex.set_context_fragment(html)
        return SebCoursewareIndex.as_view()(request, *view_args, **view_kwargs)

    def generic_error_response(self, context, request, course_key):
        """ generic error response, full page 403 error (with course menu) """
        courseware = get_courseware_module()
        try:
            course = courseware.courses.get_course(course_key, depth=2)
        except ValueError:
            return HttpResponseNotFound()

        context.update({
            'course': course,
            'request': request
        })

        return render_to_response('seb-403.html', context, status=403)

    def is_xblock_request(self, request):
        """ returns if it's an xblock HTTP request or not """
        return request.resolver_match.func.__name__ == 'handle_xblock_callback'

    @classmethod
    def is_installed(cls):
        """ Returns weather this middleware is installed in the running django instance """
        middleware_class_path = sys.modules[cls.__module__].__name__ + '.' + cls.__name__
        middlewares = settings.MIDDLEWARE_CLASSES if hasattr(settings, 'MIDDLEWARE_CLASSES') else settings.MIDDLEWARE
        return middleware_class_path in middlewares
