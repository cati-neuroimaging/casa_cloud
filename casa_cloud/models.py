import sqlite3
import docker
import os
import subprocess

from dateutil import parser
from datetime import datetime

from pyramid.security import (
    Allow,
    Everyone,
    )

glob_conn = None

def get_conn(db_path, ):
    db_path = os.path.expanduser(db_path)
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
        self.image_names = eval(settings["docker_image_names"])
        self.exposed_port = int(settings["docker_image_exposed_port"])
        self.noVNC_dir_in_container = settings["docker_image_novnc_dir"]
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.noVNC_index = os.path.join(dir_path, "..", "data", "vnc_casa.html")
        if not os.path.isfile(self.noVNC_index):
            raise ValueError("Fail to find %s" % self.noVNC_index)
        self.local_ports = local_ports

    @staticmethod
    def init_schema(conn):
        c = conn.cursor()
        sqls = []
        sqls.append("CREATE TABLE IF NOT EXISTS user_machines (user_login TEXT, container_port INTEGER UNIQUE, container_id TEXT UNIQUE, memory INTEGER, cpu_cores INTEGER, expiry_date DATE, vnc_pw TEXT)")
        for sql in sqls:
            c.execute(sql)

    def __create_docker_container(self, available_port, cpu_cores, memory, password, image, additional_options=""):
        mem_limit = "%dg" % memory
        client = docker.from_env()
        ports = {}
        ports["%d/tcp" % self.exposed_port ] = int(available_port)
        ## client.containers.run misses an parameter
        cmd = ["docker", "run", "-d", ]
        if additional_options != "":
            cmd += additional_options.split(" ")
        cmd += ["--cpus", str(cpu_cores), "--memory", mem_limit, "-p", "%d:%d" % (int(available_port), self.exposed_port), self.image_names[image]]
        out = subprocess.check_output(cmd)
        lines = out.split()
        container_id = lines[-1].strip()
        cmd = ["docker", "cp", self.noVNC_index, '%s:%s' % (container_id, self.noVNC_dir_in_container), ]
        out = subprocess.check_output(cmd)
        cmd = ["docker", "exec", "-d", container_id, 
            "/bin/bash", "-c", "echo '%s' > /tmp/pwd && cat /tmp/pwd | vncpasswd -f > $HOME/.vnc/passwd && chmod go-r $HOME/.vnc/passwd && rm /tmp/pwd" % password]
        out = subprocess.check_output(cmd)
        cmd = ["docker", "exec", "-d", container_id, "/usr/bin/vncserver", "-kill", ":1"]
        out = subprocess.check_output(cmd)
        cmd = ["docker", "exec", "-d", container_id, "/root/docker_entrypoint"]
        out = subprocess.check_output(cmd)
        return container_id

    def create_docker_container(self, available_port, cpu_cores, memory, password, image, additional_options=""):
        container_id = self.__create_docker_container(available_port, cpu_cores, memory, password, image, additional_options=additional_options)
        return container_id

    def create_machine(self, login, cpu_cores, memory, expiry_date, image, additional_options=""):
        cpu_cores = int(cpu_cores)
        memory = int(memory)
        vnc_pw = generate_temp_password(8)
        ## create a container 
        available_port = self.local_ports.allocate()
        container_id = self.create_docker_container(available_port, cpu_cores, memory, password=vnc_pw, image=image, additional_options=additional_options)
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
        print(cmd)
        os.system(cmd)
        sql = "DELETE FROM user_machines WHERE user_login='%s' and container_port=%d" % (login, int(container_port))
        c.execute(sql) 
        conn.commit()

    def search_machines(self, login=None):
        if login is not None:
            sql = "SELECT * from user_machines WHERE user_login = '%s'"% login
        else:
            sql = "SELECT * from user_machines"
        conn = get_conn(self.db_path)
        c = conn.cursor()
        ret_cursor = c.execute(sql)
        names = list(map(lambda x: x[0], ret_cursor.description))
        values = []
        for row in ret_cursor:
            values.append(row)
        return names, values

    def remove_expired_machines(self, ):
        names, values = self.search_machines()
        remove_infos = []
        for row_values in values:
            item = {}
            for i, name in enumerate(names):
                item[name] = row_values[i]
            expiry_date_str = item["expiry_date"]
            expiry_date = parser.parse(expiry_date_str)
            if expiry_date < datetime.now():
                rm_login = item["user_login"]
                rm_port = item["container_port"]
                remove_infos.append((rm_login, rm_port))
        for remove_info in remove_infos:
            rm_login, rm_port = remove_info
            self.remove_machine(login=rm_login, container_port=rm_port)

def init_schema(db_path, ):
    conn = get_conn(db_path)
    Machines.init_schema(conn)
    conn.commit()
    conn.close()


class CasaCloud(object):
    __name__ = None
    __parent__ = None
    __acl__ = [ (Allow, Everyone, 'view'),
                (Allow, 'group:casa_users', 'can_use') ]

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
