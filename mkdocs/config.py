# coding: utf-8

from mkdocs import utils
from mkdocs.compat import urlparse
import os
import yaml

DEFAULT_CONFIG = {
    'site_name': None,
    'pages': None,

    'site_url': None,
    'site_description': None,
    'site_author': None,
    'site_favicon': None,

    'theme': 'mkdocs',
    'docs_dir': 'docs',
    'site_dir': 'site',
    'theme_dir': None,

    'copyright': None,
    'google-analytics': None,

    # The address on which to serve the livereloading docs server.
    'dev_addr': '127.0.0.1:8000',

    # If `True`, use `<page_name>/index.hmtl` style files with hyperlinks to the directory.
    # If `False`, use `<page_name>.html style file with hyperlinks to the file.
    # True generates nicer URLs, but False is useful if browsing the output on a filesystem.
    'use_directory_urls': True,

    # `True` if you use server side rewriting, the user may receive some content at a different url from which it was originally rendered.
    # `False` allows you to to relocate your documentation to different url subdirectories without rebuilding.
    'use_absolute_urls': False,

    # Specify a link to the project source repo to be included
    # in the documentation pages.
    'repo_url': None,

    # A name to use for the link to the project source repo.
    # Default: If repo_url is unset then None, otherwise
    # "GitHub" or "Bitbucket" for known url or Hostname for unknown urls.
    'repo_name': None,

    # Specify which css or javascript files from the docs
    # directionary should be additionally included in the site.
    # Default: List of all .css and .js files in the docs dir.
    'extra_css': None,
    'extra_javascript': None,

    # Determine if the site should include the nav and next/prev elements.
    # Default: True if the site has more than one page, False otherwise.
    'include_nav': None,
    'include_next_prev': None,

    # Add Sitemap.xml.
    # Defulat: True.
    'include_sitemap': True,

    # These are not yet supported...
    # PyMarkdown extension names.
    'markdown_extensions': (),

    # Determine if the site should generate a json search index and include
    # search elements in the theme. - TODO
    'include_search': False,

    # Determine if the site should include a 404.html page.
    # TODO: Implment this. Make this None, have it True if a 404.html
    # template exists in the theme or docs dir.
    'include_404': False,
}


def load_config(filename='mkdocs.yml', options=None):
    options = options or {}
    if 'config' in options:
        filename = options['config']
    assert os.path.exists(filename), "Config file '%s' does not exist." % filename
    with open(filename, 'r') as fp:
        user_config = yaml.load(fp)
    user_config.update(options)
    return validate_config(user_config)


def validate_config(user_config):
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)

    assert config['site_name'], "Config must contain 'site_name' setting."

    # If not specified, then the 'pages' config simply includes all
    # markdown files in the docs dir, without generating any header items
    # for them.
    pages = []
    extra_css = []
    extra_javascript = []
    for (dirpath, dirnames, filenames) in os.walk(config['docs_dir']):
        for filename in sorted(filenames):
            fullpath = os.path.join(dirpath, filename)
            relpath = os.path.relpath(fullpath, config['docs_dir'])

            if utils.is_markdown_file(filename):
                # index pages should always be the first listed page.
                if os.path.splitext(relpath)[0] == 'index':
                    pages.insert(0, relpath)
                else:
                    pages.append(relpath)
            elif utils.is_css_file(filename):
                extra_css.append(relpath)
            elif utils.is_javascript_file(filename):
                extra_javascript.append(relpath)

    if config['pages'] is None:
        config['pages'] = pages

    if config['extra_css'] is None:
        config['extra_css'] = extra_css

    if config['extra_javascript'] is None:
        config['extra_javascript'] = extra_javascript

    if config['theme_dir'] is None:
        package_dir = os.path.dirname(__file__)
        config['theme_dir'] = os.path.join(package_dir, 'themes', config['theme'])

    package_dir = os.path.dirname(__file__)
    if not config['theme_dir']:
        config['theme_dir'] = os.path.join(package_dir, 'themes', config['theme'])

    config['statics_dir'] = os.path.join(package_dir, 'statics')

    if config['repo_url'] is not None and config['repo_name'] is None:
        repo_host = urlparse(config['repo_url']).netloc.lower()
        if repo_host == 'github.com':
            config['repo_name'] = 'GitHub'
        elif repo_host == 'bitbucket.com':
            config['repo_name'] = 'Bitbucket'
        else:
            config['repo_name'] = repo_host.split('.')[0].title()

    if config['include_next_prev'] is None:
        config['include_next_prev'] = len(config['pages']) > 1

    if config['include_nav'] is None:
        config['include_nav'] = len(config['pages']) > 1

    # To Do:

    # The docs dir must exist.
    # The theme dir must exist.
    # Ensure 'theme' is one of 'mkdocs', 'readthedocs', 'custom'
    # A homepage 'index' must exist.
    # The theme 'base.html' file must exist.
    # Cannot set repo_name without setting repo_url.
    # Cannot set 'include_next_prev: true' when only one page exists.
    # Cannot set 'include_nav: true' when only one page exists.
    # Error if any config keys provided that are not in the DEFAULT_CONFIG.

    return config
