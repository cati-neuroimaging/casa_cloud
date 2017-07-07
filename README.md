casa-cloud
==========

Remote access to CASA tools via a graphical X session in a browser.

Installation
------------


This global installation is based on the ubuntu system with apache frontend.


```
/-----------------\                               /----------\
|Apapche Frondend |   <--- casa_cloud.conf --->   |casa_cloud|
\-----------------/                               \----------/

                      \                               /-----------\
                       -----casa_novnc.conf---------> |container i|
                                                      \-----------/
                                           \
                                            \           /---------------\
                                             ---------> | container i+1 |
                                                        \---------------/
                     
```

where `casa_cloud.conf` is 

```
ProxyPass /casa_cloud http://127.0.0.1:6543
ProxyPassReverse /casa_cloud http://127.0.0.1:6543
```

and `casa_novnc.conf` is 

```
ProxyPass /novnc_30000 http://127.0.0.1:30000
ProxyPassReverse /novnc_30000 http://127.0.0.1:30000
ProxyPass /websockify_30000 ws://127.0.0.1:30000/websockify
ProxyPassReverse /websockify_30000 ws://127.0.0.1:30000/websockify


ProxyPass /novnc_30001 http://127.0.0.1:30001
ProxyPassReverse /novnc_30001 http://127.0.0.1:30001
ProxyPass /websockify_30001 ws://127.0.0.1:30001/websockify
ProxyPassReverse /websockify_30001 ws://127.0.0.1:30001/websockify

...
```



Apache Configuration
----------------------------

First you need to configure the apache frontend. We assume that your apache site configuration file is located with the path `/etc/apache2/sites-available/000-default.conf`. You can add the `Include conf.d.http/` inside of site config.

```
<VirtualHost *:80>
...
Include conf.d.http/
...
</VirtualHost>
```

You need to add the `casa_cloud.conf` and `casa_novnc.conf` into `/etc/apache2/conf.d.http`. You can see the directory structure in the `conf.d.http`.

```
$ ls /etc/apache2/conf.d.http
casa_cloud.conf  casa_novnc.conf
```

`casa_cloud.conf` is shown as above content. `casa_novnc.conf` can be generated via the below command.

```
$ cd /path/to/casa_cloud
$ ./bin/casa_cloud_init_apache_conf development.ini --apache_conf /tmp/casa_novnc.conf
$ sudo mv /tmp/casa_novnc.conf /etc/apache2/conf.d.http/
$ sudo service apache2 restart
```
