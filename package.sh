#! /bin/bash

mv game/cache cache
mv game/config config

packp3d -o naith.p3d -d game -r ode -r morepy

multify -r -f naith.p3d config
multify -r -f naith.p3d -P "#! /usr/bin/env panda3d"
chmod 755 naith.p3d

mv config game/config
mv cache game/cache
