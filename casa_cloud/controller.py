# -*- coding: utf-8 -*-

import sys, traceback
import ldap

def ldap_authenticate(request, login, password):
    ldap_server = request.registry.settings["ldap_server"]
    ldap_admin_dn = request.registry.settings["ldap_admin_dn"]
    ldap_password_file = request.registry.settings["ldap_password_file"]
    ldap_user_base_dn = request.registry.settings["ldap_user_base_dn"]
    ldap_user_login_field = request.registry.settings["ldap_user_login_field"]
    ldap_password = open(ldap_password_file, "r").read()

    ## search for user dn and then try to make a bind to check if password is correct.

    ## search for user dn
    search_filter = ldap_user_login_field + "=" + login
    searchScope = ldap.SCOPE_SUBTREE
    retrieveAttributes = None
    try:
        connect = ldap.initialize(ldap_server)
        connect.simple_bind(ldap_admin_dn, ldap_password)
        ldap_result_id = connect.search(ldap_user_base_dn, searchScope, search_filter, retrieveAttributes)
        #print("ldap_result_id=", ldap_result_id)
        result_set = []
        while 1:
            result_type, result_data = connect.result(ldap_result_id, 0)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
        if len(result_set) == 0:
            print("cannot find user %s" % login)
            return False
        user_dn = result_set[0][0][0]
        connect.unbind_s()
    except:
        print "Exception in user code:"
        print '-'*60
        traceback.print_exc(file=sys.stdout)
        print '-'*60        
        #connect.unbind_s()
        return False
    
    ## Try to bind with user password
    try:
        connect = ldap.initialize(ldap_server)
        connect.bind_s(user_dn, password)
        connect.unbind_s()
    except:
        #print("wrong password")
        #print "Exception in user code:"
        #print '-'*60
        #traceback.print_exc(file=sys.stdout)
        #print '-'*60
        return False
    #print("successful auth")
    return True

def demo_authenticate(login, password):
    ## temporarily test
    if login == "cati" and password == "cati":
        return True
    if login == "cati2" and password == "cati2":
        return True
    return False

