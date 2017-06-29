# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.parser import parse

from pyramid.view import view_config
from pyramid.security import remember
from pyramid.httpexceptions import HTTPFound

from pyramid.security import (
    Allow,
    Everyone,
    )

from pyramid.view import (
    view_config,
    forbidden_view_config,
    )

from pyramid.security import (
    remember,
    forget,
    )

from .security import USERS, check_password
from .models import CasaCloud, Machines, LocalPorts

@view_config(context='.models.CasaCloud',
             route_name='home',
             renderer='templates/index.html',
             permission="can_use",
            )
def view_home(request):
    is_success = True
    error_message = ""
    login = request.authenticated_userid
    local_ports = LocalPorts(request.registry.settings)
    machines = Machines(local_ports, request.registry.settings) 
    max_cpu_cores = int(request.registry.settings["docker_container_max_cores"])
    max_memory = int(request.registry.settings["docker_container_max_memory"])
    min_days_to_use = int(request.registry.settings["min_days_to_use"])
    if request.POST:
       if "del_machine_port" in request.POST:
           del_machine_port = request.POST["del_machine_port"]
           machines.remove_machine(login, int(del_machine_port))
       else:
           cpu_cores = request.POST["cpu_cores"]
           memory = request.POST["memory"]
           expiry_date = parse(request.POST["expiry_date"])
           diff_time = datetime.now() - expiry_date
           if diff_time.days < min_days_to_use:
               machines.create_machine(login, cpu_cores, memory, expiry_date)
           else:
               is_success = False
               error_message = "You should use at least %d days" % min_days_to_use

    names, values = machines.search_machines(login)
    render_machines = []

    for row_values in values:
        item = {}
        for i, name in enumerate(names):
            item[name] = row_values[i]
        render_machines.append(item)

    return {
             "render_machines": render_machines,
             "cpu_core_options": range(1, max_cpu_cores + 1),
             "memory_options": range(1, max_memory + 1),
             "is_success" : is_success,
             "error_message": error_message,
           }

@view_config(route_name='login', 
             renderer='templates/login.html',
             )
@forbidden_view_config(renderer='templates/login.html')
def view_login(request):
    login_url = request.resource_url(request.context, 'login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'  # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''
    if "login" in request.params and "password" in request.params:
        login = request.params['login']
        password = request.params['password']
        if check_password(USERS.get(login), password):
            #print("view_login correct login and password")
            #print("came_from=", came_from)
            headers = remember(request, login)
            return HTTPFound(location=came_from,
                             headers=headers)
        message = 'Failed login'
    return dict(
        message=message,
        url=request.application_url + '/login',
        came_from=came_from,
        login=login,
        password=password,
    )

@view_config(context='.models.CasaCloud', name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.resource_url(request.context),
                     headers=headers)

