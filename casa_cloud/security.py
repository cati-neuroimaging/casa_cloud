import bcrypt

def hash_password(pw):
    hashed_pw = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
    # return unicode instead of bytes because databases handle it better
    return hashed_pw.decode('utf-8')

def check_password(expected_hash, pw):
    if expected_hash is not None:
        return bcrypt.checkpw(pw.encode('utf-8'), expected_hash.encode('utf-8'))
    return False

USERS = {'guest': hash_password('guest'),
          'cati': hash_password('cati')}
GROUPS = {'cati':['group:cati_users']}

def groupfinder(userid, request):
    if userid in USERS:
        return GROUPS.get(userid, [])

