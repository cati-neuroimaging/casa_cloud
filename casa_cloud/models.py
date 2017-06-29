import sqlite3
import docker
import os
import subprocess

from pyramid.security import (
    Allow,
    Everyone,
    )

glob_conn = None

def get_conn(db_path, ):
    #global glob_conn
    #if glob_conn is None:
    ## sqlite cannot share connection
    glob_conn = sqlite3.connect(db_path)
    return glob_conn

def generate_temp_password(length):
    if not isinstance(length, int) or length < 8:
        raise ValueError("temp password must have positive length")

    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    from os import urandom
    return "".join(chars[ord(c) % len(chars)] for c in urandom(length))


class LocalPorts(object):
    def __init__(self, settings):
        self.db_path = settings["sqlite_data"]
        self.min_port = int(settings["local_min_available_port"])
        self.max_port = int(settings["local_max_available_port"])

    def allocate(self, ):
        conn = get_conn(self.db_path)
        c = conn.cursor()
        sql = "SELECT container_port FROM user_machines"
        used_ports = [row[0] for row in c.execute(sql)]
        for port in range(self.min_port, self.max_port):
            if port not in used_ports:
                return port
        raise ValueError("cannot find an available port "
            "between %d and %d" % (self.min_port, self.max_port))

    def release(self, port):
        ## no need to implement it since the port will be removed when a machine is removed 
        pass

class Machines(object):
    def __init__(self, local_ports, settings):
        self.db_path = settings["sqlite_data"]
        self.image_name = settings["docker_image_name"]
        self.exposed_port = int(settings["docker_image_exposed_port"])
        self.local_ports = local_ports

    @staticmethod
    def init_schema(conn):
        c = conn.cursor()
        sqls = []
        sqls.append("CREATE TABLE IF NOT EXISTS user_machines (user_login TEXT, container_port INTEGER UNIQUE, container_id TEXT UNIQUE, memory INTEGER, cpu_cores INTEGER, expiry_date DATE, vnc_pw TEXT)")
        for sql in sqls:
            c.execute(sql)

    def create_docker_container(self, available_port, cpu_cores, memory):
        
        mem_limit = "%dg" % memory
        client = docker.from_env()
        ports = {}
        ports["%d/tcp" % self.exposed_port ] = int(available_port)
        ## client.containers.run misses an parameter
        cmd = ["docker", "run", "-d", "--cpus", str(cpu_cores), "--memory", mem_limit, "-p", "%d:%d" % (int(available_port), self.exposed_port), self.image_name]
        out = subprocess.check_output(cmd)
        lines = out.split()
        container_id = lines[-1].strip()
        return container_id

    def create_machine(self, login, cpu_cores, memory, expiry_date):
        cpu_cores = int(cpu_cores)
        memory = int(memory)
        vnc_pw = generate_temp_password(8)
        ## create a container 
        available_port = self.local_ports.allocate()
        container_id = self.create_docker_container(available_port, cpu_cores, memory)
        #container_id = container.id
        sql = "INSERT INTO user_machines VALUES ('%(login)s', %(available_port)d, '%(container_id)s', %(memory)d, %(cpu_cores)d, '%(expiry_date)s', '%(vnc_pw)s')"
        data = {}
        data["login"] = login
        data["available_port"] = available_port
        data["container_id"] = container_id
        data["memory"] = int(memory)
        data["cpu_cores"] = int(cpu_cores)
        data["expiry_date"] = "%d-%d-%d" % (
            expiry_date.year,
            expiry_date.month,
            expiry_date.day,
        )
        data["vnc_pw"] = vnc_pw
        conn = get_conn(self.db_path)
        c = conn.cursor()
        c.execute(sql % data)
        conn.commit()

    def remove_machine(self, login, container_port):
        conn = get_conn(self.db_path)
        c = conn.cursor() 
        sql = "SELECT container_id FROM user_machines where user_login='%s' and container_port=%d" % (login, int(container_port))
        c.execute(sql)
        row = c.fetchone()
        container_id = row[0]
        cmd = "docker stop %s && docker rm %s" % (container_id, container_id)
        os.system(cmd)
        sql = "DELETE FROM user_machines WHERE user_login='%s' and container_port=%d" % (login, int(container_port))
        c.execute(sql) 
        conn.commit()

    def search_machines(self, login):
        sql = "SELECT * from user_machines WHERE user_login = '%s'"% login
        conn = get_conn(self.db_path)
        c = conn.cursor()
        ret_cursor = c.execute(sql)
        names = list(map(lambda x: x[0], ret_cursor.description))
        values = []
        for row in ret_cursor:
            values.append(row)
        return names, values

    def search_machine_by_login(self, login):
        pass

def init_schema(db_path, ):
    conn = get_conn(db_path)
    Machines.init_schema(conn)
    conn.commit()
    conn.close()


class CasaCloud(object):
    __name__ = None
    __parent__ = None
    __acl__ = [ (Allow, Everyone, 'view'),
                (Allow, 'group:cati_users', 'can_use') ]

def appmaker(zodb_root):
    if 'app_root' not in zodb_root:
        app_root = CasaCloud()
        zodb_root['app_root'] = app_root
    return zodb_root['app_root']

if __name__ == "__main__":
    db_path = os.path.expanduser("~/workspace/casa_cloud/data.sqlite")
    min_port = 20000
    max_port = 30000
    local_ports = LocalPorts(db_path, min_port, max_port)
    machine = Machines(db_path, "eg_sshd:latest", exposed_port=22, local_ports=local_ports)
    container = machine.create_machine(login="dddd", )