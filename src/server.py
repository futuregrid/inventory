import sys

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

inventory = Inventory("flasktest")
inventory.clean()
inventory.create("server","india[9-11].futuregrid.org,india[01-02].futuregrid.org")
print inventory.pprint()
        
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
# ROUTE: TABLE
######################################################################


@app.route('/inventory/')
def table():
    active = make_active('inventory')
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template('inventory.html',
                           updated=time_now,
                           pages=pages,
                           active=active,
                           version=version,
                           inventory=inventory)


                        
def table_printer(the_dict):
    return_str = ''
    if isinstance(the_dict, dict):
        for name,value in the_dict.iteritems() :
            return_str =return_str +'<tr><td>'+name.title() +'</td><td>'+str(table_printer(value))+'</td></tr>'
        return_str = '<table>' + return_str + '</table>'
        return return_str
    elif type(the_dict) is list: 
        for element in the_dict:
            for name,value in element.iteritems() :
                return_str =return_str +'<tr><td>'+name.title()+'</td><td>'+str(table_printer(value))+'</td></tr>'
        return_str = '<table>' + return_str + '</table>'
        return return_str
    else:
        return the_dict





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