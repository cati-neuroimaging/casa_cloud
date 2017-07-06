casa-cloud
==========

Remote access to CASA tools via a graphical X session in a browser.

Installation
------------

This installation is based on the ubuntu system with apache frontend.


```
/-----------------\                               /----------\
|Apapche Frondend |   <--- casa_cloud.conf --->   |casa_cloud|
\-----------------/                               \----------/

                      \                               /-----------\
                       -----casa_novnc.conf---------> |container i|
                                                      \-----------/
                     
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
