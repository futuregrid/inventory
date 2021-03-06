import sys
from ConfigParser import SafeConfigParser
from provisiner import *
server_config = SafeConfigParser({'name': 'flasktest'}) #Default database name
server_config.read("server.config")

from Inventory import FabricImage

sys.path.insert(0, './')
sys.path.insert(0, '../')

import json
import pprint
pp = pprint.PrettyPrinter(indent=4)

from cloudmesh.cm_keys import cm_keys
from cloudmesh.cm_projects import cm_projects
from cloudmesh.cm_config import cm_config
from cloudmesh.cloudmesh import cloudmesh

import os
import time
from flask import Flask, render_template, request,redirect
from flask_flatpages import FlatPages
import base64,struct,hashlib

from datetime import datetime
import yaml

def table_printer(the_dict, header_info=None):
    # header_info ["attribute", "value"]
    if header_info != None or (header_info == "") :
        result = '<tr><th>{0}</th><th>{1}</th></tr>'.format(header_info[0], header_info[1])
    else:
        result = ''
    if isinstance(the_dict, dict):
        for name,value in the_dict.iteritems() :
            result = result + \
                '<tr><td>{0}</td><td>{1}</td></tr>'.format(name.title(),
                                                           str(table_printer(value)))
        result = '<table>' + result + '</table>'
        return result
    elif type(the_dict) is list: 
        for element in the_dict:
            for name,value in element.iteritems() :
                result =result +\
                    '<tr><td>{0}</td><td>{1}</td></tr>'.format(name.title(),
                                                               str(table_printer(value)))
        result = '<table>' + result + '</table>'
        return result 
    else:
        return the_dict


######################################################################
# allowing the yaml file to be written back upon change
######################################################################

with_write = True

######################################################################
# setting up reading path for the use of yaml
######################################################################

default_path = '.futuregrid/cloudmesh.yaml'
home = os.environ['HOME']
filename = "%s/%s" % (home, default_path)

######################################################################
# global vars
######################################################################

DEBUG = True
FLATPAGES_AUTO_RELOAD = DEBUG
FLATPAGES_EXTENSION = '.md'

"""
import pkg_resources
version = pkg_resources.get_distribution("flask_cm").version
"""
version = "0.1"

######################################################################
# INVENTORY
######################################################################

from Inventory import Inventory
from Inventory import FabricService
from Inventory import FabricServer

inventory_db = server_config.get("mongo", "dbname")
if server_config.has_option("mongo", "host"):
    inventory = Inventory(inventory_db,
                          server_config.get("mongo", "host"),
                          server_config.getint("mongo", "port"),
                          server_config.get("mongo", "user"),
                          server_config.get("mongo", "pass"))
else:
    inventory = Inventory(inventory_db)
inventory.clean()

inventory.create_cluster("brave", "101.102.203.[11-26]", "b{0:03d}", 1, "b001", "b")
#inventory.create_cluster("delta", "102.202.204.[1-16]", "d-{0:03d}", 1, "d-001", "d")
#inventory.create_cluster("gamma", "302.202.204.[1-16]", "g-{0:03d}", 1, "g-001", "g")
#inventory.create_cluster("india", "402.202.204.[1-128]", "i-{0:03d}", 1, "i-001", "i")
#inventory.create_cluster("sierra", "502.202.204.[1-128]", "s-{0:03d}", 1, "s-001", "s")

centos = FabricImage(
    name = "centos6",
    osimage = '/path/to/centos0602v1-2013-06-11.squashfs',
    os = 'centos6',
    extension = 'squashfs',
    partition_scheme = 'mbr',
    method = 'put',
    kernel = 'vmlinuz-2.6.32-279.19.1.el6.x86_64',
    ramdisk = 'initramfs-2.6.32-279.19.1.el6.x86_64.img',
    grub = 'grub',
    rootpass = 'reset'
).save()

redhat = FabricImage(
    name = "ubuntu",
    osimage = '/BTsync/ubuntu1304/ubuntu1304v1-2013-06-11.squashfs',
    os = 'ubuntu',
    extension = 'squashfs',
    partition_scheme = 'mbr',
    method = 'btsync',
    kernel = 'vmlinuz-2.6.32-279.19.1.el6.x86_64',
    ramdisk = 'initramfs-2.6.32-279.19.1.el6.x86_64.img',
    grub = 'grub2',
    rootpass = 'reset'
).save()



print inventory.pprint()

######################################################################
# PROVISINOR
######################################################################
provisionerImpl = ProvisionerSimulator

provisioner = provisionerImpl()


######################################################################
# STARTING THE FLASK APP
######################################################################

app = Flask(__name__)
app.config.from_object(__name__)
pages = FlatPages(app)

######################################################################
# ACTIVATE STRUCTURE
######################################################################


def make_active(name):
    active = {'home': "",
              'inventory': "",
              "images":"",
              'contact': "",
              'profile': ""}
    
    active[name] = 'active'
    return active

######################################################################
# ROUTE: /
######################################################################


@app.route('/')
def index():
    active = make_active('home')
    return render_template('index.html',
                           pages=pages,
                           active=active,
                           version=version)

######################################################################
# ROUTE: SAVE
######################################################################


@app.route('/inventory/save/')
def save():
    print "Saving the inventory"
    return display_inventory()

######################################################################
# ROUTE: LOAD
######################################################################


@app.route('/inventory/load/')
def load():
    print "Loading the inventory"
    return display_inventory()

######################################################################
# ROUTE: INVENTORY TABLE
######################################################################


@app.route('/inventory/')
def display_inventory():
    active = make_active('inventory')
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template('inventory.html',
                           updated=time_now,
                           pages=pages,
                           active=active,
                           version=version,
                           inventory=inventory)

@app.route('/inventory/cluster/<cluster>/')
def display_cluster(cluster):
    active = make_active('inventory')
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template('inventory_cluster.html',
                           updated=time_now,
                           pages=pages,
                           active=active,
                           version=version,
                           cluster=inventory.find("cluster", cluster))



@app.route('/inventory/images/<name>/')
def display_image(name):
    active = make_active('')
    image= inventory.get ('image', name)[0]
    return render_template('info_image.html',
                           table_printer=table_printer,
                           image=image.data,
                           name=name,
                           pages=pages,
                           active=active,
                           version=version,
                           inventory=inventory)

@app.route('/inventory/images/')
def display_images():
    active = make_active('images')
    return render_template('images.html',
                           pages=pages,
                           active=active,
                           version=version,
                           inventory=inventory)

######################################################################
# ROUTE: INVENTORY ACTIONS
######################################################################

@app.route('/inventory/info/server/<server>/')
def server_info(server):
    active = make_active('')
    
    server = inventory.find("server", name)
    return render_template('info_server.html',
                           server=server,
                           pages=pages,
                           active=active,
                           version=version,
                           inventory=inventory)


@app.route('/inventory/set/service/', methods=['POST'])
def set_service():
    server = request.form['server']
    service = request.form['service']

    active = make_active('inventory')
    inventory.set_service('%s-%s' % (server, service), server, service)
    provisioner.provision([server], service)    
    return display_inventory()

@app.route('/inventory/set/attribute/', methods=['POST'])
def set_attribute():
    kind = request.form['kind']
    name = request.form['name']
    attribute = request.form['attribute']
    value = request.form['value']

    active = make_active('inventory')
    s = inventory.get (kind, name)
    s[attribute] = value
    s.save()
    return display_inventory()

@app.route('/inventory/get/<kind>/<name>/<attribute>')
def get_attribute():
    active = make_active('inventory')
    s = inventory.get (kind, name)
    return s[attribute]

##############################
# Helpers
##############################
    




######################################################################
# ROUTE: PAGES
######################################################################


@app.route('/<path:path>/')
def page(path):
    active = make_active(str(path))
    page = pages.get_or_404(path)
    return render_template('page.html',
                           page=page,
                           pages=pages,
                           active=active,
                           version=version)


    
if __name__ == "__main__":
    app.run()
