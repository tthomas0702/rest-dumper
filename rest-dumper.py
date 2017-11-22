#!/usr/bin/python

# rest config dumper to excersize API 
# ver 0.0.3


from f5.bigip import ManagementRoot
import optparse
import sys
from pprint import pprint
import random
import time

# disable insuecure warnings
import requests
# This one works on my opti
requests.packages.urllib3.disable_warnings()
 
# this one works on rapidlab ubunt...choose the above if this does not work 
#import urllib3
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


parser = optparse.OptionParser()

parser.add_option(
    '-d',
    '--debug',
    dest="debug",
    default=False,
    action="store_true",
    help="Print out arg values given"
    )

parser.add_option(
    '-u',
    '--user',
    dest="remUser",
    default='admin',
    action="store",
    help="Remote user name"
    )

parser.add_option(
    '-p',
    '--pass',
    dest="remPass",
    default='admin',
    action="store",
    help="Remote user name"
    )

parser.add_option(
    '-a',
    '--address',
    dest="address",
    action="store",
    help="address of remote device"
    )

parser.add_option(
    '-n',
    '--name',
    dest="namePrefix",
    action="store",
    help="global name prefix for the opbject group being created"
    )

parser.add_option(
    '-t',
    '--target',
    dest="target",
    default="x.x.x.x",
    action="store",
    help="address that will be used in example if -e is used"
    )

parser.add_option(
    '-v',
    '--vs',
    dest="vsAddress",
    action="store",
    help="address that will be used for Virtual server destination"
    )


parser.add_option(
    '-r',
    '--remove',
    dest="removeAfterSeconds",
    action="store",
    help="Take arg of second and will remove objects created after sleeping for n seconds, if not present will not remove"
    )


#print(parser.parse_args())

options, remainder = parser.parse_args()

# check for needed opts
if not options.address: # if -a not give
    parser.error('IP address/host not given')

if not options.namePrefix: # if -n not given
    parser.error('-n is required')

if not options.vsAddress: # is no virtual server dest given
    parser.error('-v is required')


# Connect to the BIG-IP
mgmt = ManagementRoot(options.address, options.remUser, options.remPass)


#### make  a lot data-group ####
# open test file with data-group values in it
dgValues = open('include_rest-dumper/data_group.txt', 'r').read()

dataGroupNameList  = []    # This will be used to delete as well
dataGroupName1 = options.namePrefix + "_data_group"
# set number of rules to make
for i in range(1,69):
    dataGroupNameList.append(dataGroupName1 + str(i))

for dgName in dataGroupNameList:
    dataGroup1 =  mgmt.tm.ltm.data_group.internals.internal.create(
        name= dgName,
        type= 'string',
        records= [ dgValues ]
        )


# clean data-groups example
#time.sleep(30)
#for dgName in dataGroupNameList:
#    delDataGroup = mgmt.tm.ltm.data_group.internals.internal.load(name= dgName )
#    delDataGroup.delete()





#### make rules , lots of them ##

# make list of names
iruleName1 = options.namePrefix + "_irule"
ruleNameList = []    # This will be used to delete as well
# set number of rules to make
for i in range(1,50):
    ruleNameList.append(iruleName1 + str(i))
# open on test file that has the irule code I will use
iruleCode = open('include_rest-dumper/irule1.txt', 'r').read()

# create rules
for ruleName in ruleNameList:
    irule1 = mgmt.tm.ltm.rules.rule.create(name= ruleName, partition = 'Common', apiAnonymous= iruleCode)

# logger irule
iruleCode = open('include_rest-dumper/irule1.txt', 'r').read()
logRuleName = options.namePrefix + "_logger_irule"
loggerIrule = mgmt.tm.ltm.rules.rule.create(name= logRuleName, partition = 'Common', apiAnonymous= iruleCode)


# cleanup irule example
#time.sleep(20)
#for ruleName in ruleNameList:
#    delRule = mgmt.tm.ltm.rules.rule.load(name= ruleName, partition = 'Common')
#    delRule.delete()
#delLoggerIrule = mgmt.tm.ltm.rules.rule.load(name= 'logger', partition = 'Common')
#delLoggerIrule.delete()



#### make certs for profile ####

keyName = options.namePrefix + "_key"
certName = options.namePrefix + "_cert"
# here is how to do it when file is on BIG-IP
#key1 = mgmt.tm.sys.file.ssl_keys.ssl_key.create(name= keyName, partition='Common', sourcePath='file:/var/tmp/fake1_1.key')
#cert1 = mgmt.tm.sys.file.ssl_certs.ssl_cert.create(name= certName, partition='Common', sourcePath='file:/var/tmp/fake1_1.crt')
# Here is how to use certs on web server
key1 = mgmt.tm.sys.file.ssl_keys.ssl_key.create(name= keyName, partition='Common', sourcePath='http://10.1.212.8/fake1_1.key')
cert1 = mgmt.tm.sys.file.ssl_certs.ssl_cert.create(name= certName, partition='Common', sourcePath='http://10.1.212.8/fake1_1.crt')

#### make client-ssl profile ####

sslProfileClientsideName1 = options.namePrefix + "_client_ssl_profile"
clientSslProfile1 = mgmt.tm.ltm.profile.client_ssls.client_ssl.create(name= sslProfileClientsideName1 , partition='Common', ciphers= 'DEFAULT:!RSA', cert= certName, key= keyName)

# cleanup profile and cert/key example
#time.sleep(30)
#clientSslProfile1.delete()
#cert1.delete()
#key1.delete()




#### make http profile ####

httpProfileName = options.namePrefix + "_http_profile"
httpProfile = mgmt.tm.ltm.profile.https.http.create(name= httpProfileName )
httpProfile = mgmt.tm.ltm.profile.https.http.load(name= httpProfileName)
httpProfile.enforcement = { 'maxHeaderCount' : '60', 'maxHeaderSize' : '3200'}
httpProfile.insertXforwardedFor = 'enabled'
httpProfile.update()

## cleanup http profile ##
#httpProfile.delete()



#### Make Pool ####

#create a pool

def makePool(poolName, port, memberNet, mon, part):
    mgmt.tm.ltm.pools.pool.create(name = poolName, partition=part, monitor=mon)

    # Define a pool object and load an existing pool
    poolObj = mgmt.tm.ltm.pools.pool.load(partition=part, name= poolName )
    poolObj.description = "This is " + poolName
    poolObj.update()

    # Create members on poolObj
    members = poolObj.members_s
    member = poolObj.members_s.members

    n = str(random.randint(2,253))
    pm1 = memberNet + n + ':' + port
    n = str(random.randint(2,253))
    pm2 = memberNet + n + ':' + port

    m1 = poolObj.members_s.members.create(partition=part, name= pm1)
    m2 = poolObj.members_s.members.create(partition=part, name= pm2)

    # load the pool members(maybe shoudl remove this)
    #m1 = poolObj80.members_s.members.load(partition='Common', name= pm1)
    #m2 = poolObj80.members_s.members.load(partition='Common', name= pm2)

    return poolObj

#call makePool for port 80 pool
poolName = options.namePrefix + "_pool_80"
port = '80'
memberNet = '10.2.211.'
mon = 'tcp'
part = 'Common'
poolObj80 = makePool(poolName, port, memberNet, mon, part)

# call to make 443 pool
poolName = options.namePrefix + "_pool_443"
port = '443'
memberNet = '10.2.108.'
mon = 'https'
part = 'Common'
poolObj443 = makePool(poolName, port, memberNet, mon, part)



# Delete pool 80 example 
#time.sleep(30)
# poolObj80.delete()

# Delete pool 443  example 
#time.sleep(30)
# poolObj443.delete()

#### end pool ###


#### make virutals ####
# port 80 
destAndPort80 = options.vsAddress + ':80'
virtName = options.namePrefix + "_vs"
print "creating VS ", virtName
vip80 = mgmt.tm.ltm.virtuals.virtual.create(
    name= virtName, 
    partition='Common', 
    type= 'Standard', 
    destination= destAndPort80,
    mask= '255.255.255.255',
    ipProtocol= 'tcp',    
    sourceAddressTranslation= {'type':'automap'},
    pool= poolObj80.fullPath

)

# now add some stuff to the virtual above
vip80 = mgmt.tm.ltm.virtuals.virtual.load(name= virtName)
vip80.profiles = [
        {'name' : httpProfileName,'context': 'all', "partition": "Common"}, 
        {'name' : 'oneconnect', 'context': 'all', 'partition': 'Common'},
        {'name' : 'f5-tcp-wan', 'context': 'clientside', 'partition': 'Common'},
        {'name' : 'f5-tcp-lan', 'context': 'serverside', 'partition': 'Common'}        
    ]
vip80.persist = ['cookie']
vip80.fallbackPersistence = '/Common/source_addr'
vip80.rules = [logRuleName, ruleNameList[0], ruleNameList[2], ruleNameList[2], ruleNameList[3], ruleNameList[4], ruleNameList[5]]
vip80.update()

## cleanup vip example ##
#vip80.delete()

# port 443
destAndPort443 = options.vsAddress + ':443'
virtName443 = options.namePrefix + "_vs_443"
print "creating VS ", virtName443
vip443 = mgmt.tm.ltm.virtuals.virtual.create(
    name= virtName443,
    partition='Common',
    type= 'Standard',
    destination= destAndPort443,
    mask= '255.255.255.255',
    ipProtocol= 'tcp',
    sourceAddressTranslation= {'type':'automap'},
    pool= poolObj443.fullPath

)

# now add some stuff to the virtual above
vip443 = mgmt.tm.ltm.virtuals.virtual.load(name= virtName443)
vip443.profiles = [
        {'name' : httpProfileName,'context': 'all', "partition": "Common"},
        {'name' : 'oneconnect', 'context': 'all', 'partition': 'Common'},
        {'name' : 'f5-tcp-wan', 'context': 'clientside', 'partition': 'Common'},
        {'name' : 'f5-tcp-lan', 'context': 'serverside', 'partition': 'Common'},
        {'name' : sslProfileClientsideName1, 'context': 'clientside', 'partition': 'Common'},
        {'name' : 'serverssl', 'context': 'serverside', 'partition': 'Common'}
    ]
vip443.persist = ['cookie']
vip443.fallbackPersistence = '/Common/source_addr'
vip443.rules = [logRuleName, ruleNameList[0], ruleNameList[2], ruleNameList[2], ruleNameList[3], ruleNameList[4], ruleNameList[5]]
vip443.update()


## cleanup vip example ##
#vip443.delete()


#### next clean up if -r is given ####


if options.removeAfterSeconds:
    delay = int(options.removeAfterSeconds)
    print "Delaying for {0} before removing objects".format(delay)
    time.sleep(delay)

    # remove virtuals
    print "removing vs ", vip80.name
    vip80.delete()
    print "removing vs ", vip443.name
    vip443.delete()

    # remove pools
    print "removing pool ", poolObj80.name
    poolObj80.delete()
    print "removing pool ", poolObj443.name
    poolObj443.delete()

    # remove data-groups
    print "Deleting data-groups "
    for dgName in dataGroupNameList:
        delDataGroup = mgmt.tm.ltm.data_group.internals.internal.load(name= dgName )
        #print "Deleting data-groups ", delDataGroup.name
        delDataGroup.delete()

    # remove irules
    print "removing irule "
    for ruleName in ruleNameList:
        delRule = mgmt.tm.ltm.rules.rule.load(name= ruleName, partition = 'Common')
        #print "removing irule ", delRule.name
        delRule.delete()

    # remove logger irule
    delLoggerIrule = mgmt.tm.ltm.rules.rule.load(name= logRuleName, partition = 'Common')
    #print "removing irule ", delLoggerIrule.name
    delLoggerIrule.delete()
    
    # remove client SSL profile, cert, and key
    print "removing Client SSL profile ", clientSslProfile1.name
    clientSslProfile1.delete()
    print "removing cert ", cert1.name
    cert1.delete()
    print "removing key ", key1.name
    key1.delete()

    # remove http profile
    print "remvoing http profile ", httpProfile.name
    httpProfile.delete()    
























