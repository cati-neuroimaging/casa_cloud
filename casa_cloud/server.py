# -*- coding: utf-8 -*-

import os

from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from .models import appmaker
from .security import groupfinder

def root_factory(request):
    data = {}
    return appmaker(data)

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    authn_policy = AuthTktAuthenticationPolicy(
        'sosecret', callback=groupfinder, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()

    settings["sqlite_data"] = os.path.expanduser(settings["sqlite_data"])

    config = Configurator(root_factory=root_factory, settings=settings)
    settings = config.get_settings()

    settings['tm.manager_hook'] = 'pyramid_tm.explicit_manager'
    website_base_url = settings["website_base_url"]
    if website_base_url.endswith("/"):
        website_base_url = website_base_url[:-1]
    settings["website_base_url"] = website_base_url
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.include('pyramid_jinja2')
    config.include('pyramid_chameleon')
    config.include('pyramid_tm')
    config.include('pyramid_retry')
    config.include('pyramid_zodbconn')

    config.add_jinja2_renderer('.html')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.scan()
    return config.make_wsgi_app()

