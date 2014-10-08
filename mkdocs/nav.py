# coding: utf-8

"""
Deals with generating the site-wide navigation.

This consists of building a set of interlinked page and header objects.
"""

from mkdocs import utils
import posixpath
import os
import time


def filename_to_title(filename):
    """
    Automatically generate a default title, given a filename.
    """
    if utils.is_homepage(filename):
        return 'Home'

    title = os.path.splitext(filename)[0]
    title = title.replace('-', ' ').replace('_', ' ')
    # Captialize if the filename was all lowercase, otherwise leave it as-is.
    if title.lower() == title:
        title = title.capitalize()
    return title


class SiteNavigation(object):
    def __init__(self, pages_config, site_url, use_directory_urls=True, use_absolute_urls=False):
        self.url_context = URLContext(site_url, use_absolute_urls)
        self.file_context = FileContext()
        self.nav_items, self.pages = \
            _generate_site_navigation(pages_config, self.url_context, use_directory_urls)
        self.homepage = self.pages[0] if self.pages else None
        self.use_absolute_urls = use_absolute_urls
        self.use_directory_urls = use_directory_urls

    def __str__(self):
        return str(self.homepage) + ''.join([str(item) for item in self])

    def __iter__(self):
        return iter(self.nav_items)

    def walk_pages(self):
        """
        Returns each page in the site in turn.

        Additionally this sets the active status of the pages and headers,
        in the site navigation, so that the rendered navbar can correctly
        highlight the currently active page and/or header item.
        """
        prev_page = None
        for page in self.pages:
            if prev_page != None:
                prev_page.set_active(False)
            page.set_active()
            prev_page = page
            self.url_context.set_current_url(page.abs_url)
            self.file_context.set_current_path(page.input_path)
            yield page
        prev_page.set_active(False)

    @property
    def source_files(self):
        if not hasattr(self, '_source_files'):
            self._source_files = set([page.input_path for page in self.pages])
        return self._source_files


class URLContext(object):
    """
    The URLContext is used to ensure that we can generate the appropriate
    relative URLs to other pages from any given page in the site.

    We use relative URLs so that static sites can be deployed to any location
    without having to specify what the path component on the host will be
    if the documentation is not hosted at the root path.
    """

    def __init__(self, site_path, use_absolute_urls=False):
        self.base_path = '/'
        self.site_path = site_path
        self.use_absolute_urls = use_absolute_urls

    def set_current_url(self, current_url):
        self.base_path = posixpath.dirname(current_url)

    def make_relative(self, url):
        """
        Given a URL path return it as a relative URL,
        given the context of the current page.
        """
        if self.use_absolute_urls:
            return self.site_path + url.lstrip('/')
        else:
            suffix = '/' if (url.endswith('/') and len(url) > 1) else ''
            # Workaround for bug on `posixpath.relpath()` in Python 2.6
            if self.base_path == '/':
                if url == '/':
                    # Workaround for static assets
                    return '.'
                return url.lstrip('/')
            return posixpath.relpath(url, start=self.base_path) + suffix


class FileContext(object):
    """
    The FileContext is used to ensure that we can generate the appropriate
    full path for other pages given their relative path from a particular page.

    This is used when we have relative hyperlinks in the documentation, so that
    we can ensure that they point to markdown documents that actually exist
    in the `pages` config.
    """
    def __init__(self):
        self.current_file = None
        self.base_path = ''

    def set_current_path(self, current_path):
        self.current_file = current_path
        self.base_path = os.path.dirname(current_path)

    def make_absolute(self, path):
        """
        Given a relative file path return it as a POSIX-style
        absolute filepath, given the context of the current page.
        """
        return posixpath.normpath(posixpath.join(self.base_path, path))


class Page(object):
    def __init__(self, title, url, path, url_context):
        self.title = title
        self.abs_url = url
        self.active = False
        self.url_context = url_context
        self.update_date = time.strftime('%Y-%m-%d', time.gmtime())

        # Relative paths to the input markdown file and output html file.
        self.input_path = path
        self.output_path = utils.get_html_path(path)

        # Links to related pages
        self.previous_page = None
        self.next_page = None
        self.ancestors = []

    @property
    def url(self):
        return self.url_context.make_relative(self.abs_url)

    @property
    def is_homepage(self):
        return utils.is_homepage(self.input_path)

    def __str__(self):
        return self._indent_print()

    def _indent_print(self, depth=0):
        indent = '    ' * depth
        active_marker = ' [*]' if self.active else ''
        title = self.title if (self.title is not None) else '[blank]'
        return '%s%s - %s%s\n' % (indent, title, self.abs_url, active_marker)

    def set_active(self, active=True):
        self.active = active
        for ancestor in self.ancestors:
            ancestor.active = active


class Header(object):
    def __init__(self, title, children):
        self.title, self.children = title, children
        self.active = False

    def __str__(self):
        return self._indent_print()

    def _indent_print(self, depth=0):
        indent = '    ' * depth
        active_marker = ' [*]' if self.active else ''
        ret = '%s%s%s\n' % (indent, self.title, active_marker)
        for item in self.children:
            ret += item._indent_print(depth + 1)
        return ret


def _generate_site_navigation(pages_config, url_context, use_directory_urls=True):
    """
    Returns a list of Page and Header instances that represent the
    top level site navigation.
    """
    nav_items = []
    pages = []
    previous = None
    hidden_previous = None

    for config_line in pages_config:
        if isinstance(config_line, str):
            path = config_line
            title, child_title = None, None
        elif len(config_line) in (1, 2, 3):
            # Pad any items that don't exist with 'None'
            padded_config = (list(config_line) + [None, None])[:3]
            path, title, child_title = padded_config
        else:
            msg = (
                "Line in 'page' config contained %d items.  "
                "Expected 1, 2 or 3 strings." % len(config_line)
            )
            assert False, msg

        if title is None:
            filename = path.split('/')[0]
            title = filename_to_title(filename)
        if child_title is None and '/' in path:
            filename = path.split('/')[1]
            child_title = filename_to_title(filename)

        url = utils.get_url_path(path, use_directory_urls)

        if not child_title or title == '**HIDDEN**':
            # New top level page.
            page = Page(title=title, url=url, path=path, url_context=url_context)
            if (page.title is not None and
                    title != '**HIDDEN**' and
                    not utils.is_homepage(path)):
                # Page config lines that do not include a title, such as:
                #    - ['index.md']
                # Will not be added to the nav items heiarchy, although they
                # are included in the full list of pages, and have the
                # appropriate 'next'/'prev' links generated.
                nav_items.append(page)
        elif not nav_items or (nav_items[-1].title != title):
            # New second level page.
            page = Page(title=child_title, url=url, path=path, url_context=url_context)
            header = Header(title=title, children=[page])
            nav_items.append(header)
            page.ancestors = [header]
        else:
            # Additional second level page.
            page = Page(title=child_title, url=url, path=path, url_context=url_context)
            header = nav_items[-1]
            header.children.append(page)
            page.ancestors = [header]

        # Add in previous and next information.
        if previous:
            page.previous_page = previous
            previous.next_page = page

        if hidden_previous != None:
            hidden_previous.next_page = page

        if title == '**HIDDEN**':
            hidden_previous = page
        else:
            hidden_previous = None
            previous = page

        pages.append(page)

    return (nav_items, pages)
