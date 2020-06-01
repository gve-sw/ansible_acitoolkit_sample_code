""" Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
           https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

import acitoolkit as aci
from acitoolkit import Credentials, Session, Tenant, AppProfile, EPG, PortChannel
import sys
import credentials
import subprocess
import yaml
import os


def get_epg(session, tenant):

    """
    Get the EPG
    :param session: Session class instance
    :param tenant: String containing the Tenant name
    """
    apps = AppProfile.get(session, tenant)

    if len(apps) == 0:
        print("No APs for this tenant")
    
    else:
        for app in apps:
            epgs = EPG.get(session, app, tenant)
            if len(epgs) == 0:
                print("No EPGS for this AP: ",app)
            else:
                for epg in epgs:
                    print("Epg:" ,epg.name, "AP: ",app.name)
                    print("----------")
                epg_name = input("Select name of EPG: ")
                for epg in epgs:
                    if epg_name == epg.name:
                        print("EPG exists")
                        return epg
            print("EPG does not exist")

def get_phy_domain(session,epg):
    counter = 0
    list_domains = []

    domains = aci.EPGDomain.get(session)
    for domain in domains:
        if domain.domain_type == 'phys':
            if domain.epg_name == epg.name:
                print(domain.dn)
                list_domains.append(domain.dn)
                counter = counter + 1
    return list_domains
                

dirname = os.path.dirname(__file__)

# Login to APIC
description = ('simple python script.')
creds = Credentials('apic', description)
creds.add_argument('--tenant', help='The name of Tenant')
session = Session(credentials.url, credentials.username, credentials.password)
resp = session.login()

if resp.ok:
    print("Login to APIC sucessful")
else:
    (print("Error logging into APC, please check the ip address and credentials"))

port_channels = aci.PortChannel.get(session)
tenants = aci.Tenant.get(session)

print(len(tenants)," amount of tenants")
print("----------")

for tenant in tenants:
    print(tenant.name)
    print("----------")

tenant_name = input("Choose which tenant you would like to select:")

for tenant in tenants:
    if tenant_name == tenant.name:
        epg = get_epg(session, tenant)
        list_of_domains = get_phy_domain(session,epg)

        print("List of Physical Domains from ",tenant.name)

        domains = aci.PhysDomain.get(session)
        for domain in domains:
            print(domain.name)
            print("----------")

        temp = epg.dn.split('/')
        domain = input("Choose which physical domain to add: ")

        filename = os.path.join(dirname, 'ansible/vars/vars_domain_binding.yaml')

        with open(filename) as file:
            variables = yaml.load(file,Loader=yaml.FullLoader)

            variables["host"] = credentials.ip_address
            variables["username"] = credentials.username
            variables["password"] = credentials.password
            variables["tenant"] = temp[1].split('-')[1]
            variables["ap"] = temp[2].split('-')[1]
            variables["epg"] = temp[3].split('-')[1]
            variables["domain"] = domain
        
        filename = os.path.join(dirname, 'ansible/vars/vars_domain_binding.yaml')

        with open(filename, "w") as file:
            yaml.dump(variables, file)
        
        filename = os.path.join(dirname, 'ansible/bind_physd_epg.yaml')

        subprocess.run(['ansible-playbook',filename])
        p = subprocess.Popen(['tail', '/var/log/syslog'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate()

        print("Physical Domain has been added to EPG!")

        response = input("Press Y to add this epg to a VPC:")

        if response.lower() == "y":
            print("Y pressed!")

            channels = PortChannel.get(session)

            print(len(channels),"amount of VPCs")
            print("----------")

            for channel in channels:
                print(channel.name)
                print("----------")

            vpc = input("Enter which VPC you would like to use:")
            
            filename = os.path.join(dirname, 'ansible/vars/vars_epg_binding.yaml')

            with open(filename) as file:
                variables = yaml.load(file,Loader=yaml.FullLoader)

                variables["host"] = credentials.ip_address
                variables["username"] = credentials.username
                variables["password"] = credentials.password
                variables["tenant"] = temp[1].split('-')[1]
                variables["ap"] = temp[2].split('-')[1]
                variables["epg"] = temp[3].split('-')[1]
                variables["domain"] = domain
                variables["vpc"] = vpc
         
            filename = os.path.join(dirname, 'ansible/vars/vars_epg_binding.yaml')

            with open(filename, "w") as file:
                yaml.dump(variables, file)
            
            filename = os.path.join(dirname, 'ansible/vpc_epg.yaml')

            subprocess.run(['ansible-playbook',filename])
            p = subprocess.Popen(['tail', '/var/log/syslog'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.communicate()
    
        else:
            exit()




