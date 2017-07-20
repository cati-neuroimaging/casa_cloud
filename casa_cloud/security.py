import bcrypt
import importlib

#def demo_authenticate(request, login, password):
#    ## temporarily test
#    if login == "cati" and password == "cati":
#        return True
#    if login == "cati2" and password == "cati2":
#        return True
#    return False

def authenticate(request, login, password):
    authenticate_function_path = request.registry.settings["authenticate_function"]
    authenticate_function_parts = authenticate_function_path.split(".")
    function_name = authenticate_function_parts[-1]
    module_path = authenticate_function_parts[:-1]
    module_path = ".".join(module_path)
    #print("module_path=", module_path)
    #print("function_name=", function_name)
    default_auth_module = importlib.import_module(module_path)
    authenticate_function = getattr(default_auth_module, function_name)
    return authenticate_function(login, password)

#def hash_password(pw):
#    hashed_pw = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
#    # return unicode instead of bytes because databases handle it better
#    return hashed_pw.decode('utf-8')
#def check_password(expected_hash, pw):
#    if expected_hash is not None:
#        return bcrypt.checkpw(pw.encode('utf-8'), expected_hash.encode('utf-8'))
#    return False
#USERS = {'guest': hash_password('guest'),
#          'cati': hash_password('cati')}
#GROUPS = {'cati':['group:cati_users']}
#

def groupfinder(userid, request):
    return ['group:casa_users', ]

