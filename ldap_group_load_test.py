#! /usr/bin/env python

from __future__ import division, print_function
import argparse
import datetime
from twisted.internet import reactor, defer
from twisted.internet.endpoints import clientFromString, connectProtocol
from twisted.internet.task import react
from twisted.python import log
from ldaptor import delta
from ldaptor.protocols.ldap.ldapclient import LDAPClient
from ldaptor.protocols.ldap.ldapsyntax import LDAPEntry
from ldaptor.protocols import (
    pureber,
    pureldap
)
from six import string_types
import sys


@defer.inlineCallbacks
def onConnect(client, args):
    yield client.startTLS()
    binddn = args.binddn
    passwd = args.passwd_file.read().strip()
    yield client.bind(args.binddn, passwd)
    add_memberof = delta.ModifyOp(
        args.entrydn,
        [
            delta.Add('memberOf', [args.groupdn]),
        ])
    delete_memberof = delta.ModifyOp(
        args.entrydn,
        [
            delta.Delete('memberOf', [args.groupdn]),
        ])
    add_member = delta.ModifyOp(
        args.groupdn,
        [
            delta.Add('member', [args.entrydn]),
        ])
    delete_member = delta.ModifyOp(
        args.groupdn,
        [
            delta.Delete('member', [args.entrydn]),
        ])
    req_add_memberof = add_memberof.asLDAP()
    req_delete_memberof = delete_memberof.asLDAP()
    req_add_member = add_member.asLDAP()
    req_delete_member = delete_member.asLDAP()
    total_time = 0
    total_changes = 0
    for n in range(args.iterations):
        start = datetime.datetime.now()
        yield defer.gatherResults([
            send_request(client, req_add_memberof),
            send_request(client, req_add_member)])
        end = datetime.datetime.now()
        elapsed = (end - start).total_seconds()
        total_time += elapsed
        total_changes += 1
        start = datetime.datetime.now()
        yield defer.gatherResults([
            send_request(client, req_delete_memberof),
            send_request(client, req_delete_member)])
        end = datetime.datetime.now()
        elapsed = (end - start).total_seconds()
        total_time += elapsed
        total_changes += 1
    mean_time = total_time / total_changes
    print("Mean time in seconds for a membership change: {}".format(mean_time))

@defer.inlineCallbacks
def send_request(client, req):
    response = yield client.send(req)
    resultCode = response.resultCode
    if response.resultCode != 0:
        errorMessage = response.errorMessage
        log.err(
            "DIT reported error code {}: {}".format(resultCode, errorMessage))

def onError(err, reactor):
    if reactor.running:
        log.err(err)
        reactor.stop()

def main(reactor, args):
    log.startLogging(sys.stdout)
    endpoint_str = args.endpoint 
    e = clientFromString(reactor, endpoint_str)
    d = connectProtocol(e, LDAPClient())
    d.addCallback(onConnect, args)
    d.addErrback(onError, reactor)
    return d

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LDAP test client.")
    parser.add_argument(
        "endpoint",
        action="store",
        help="See https://twistedmatrix.com/documents/current/core/howto/endpoints.html#clients")
    parser.add_argument(
        "binddn",
        action="store",
        help="The DN to BIND to the service as.")
    parser.add_argument(
        "passwd_file",
        action="store",
        type=argparse.FileType('r'),
        help="A file containing the password used to log into the service.")
    parser.add_argument(
        "entrydn",
        action="store",
        help="The DN of the entry.")
    parser.add_argument(
        "groupdn",
        action="store",
        help="The DN of the group.")
    parser.add_argument(
        "-i",
        "--iterations",
        action="store",
        type=int,
        default=1,
        help="The number of iterations.")
    args = parser.parse_args()
    react(main, [args])

