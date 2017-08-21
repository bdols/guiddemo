#!/usr/bin/env python3
# A sample GUID API client

import argparse
import json
import re
import requests
from requests.utils import urlparse
import string
import time

__version__ = '0.1'

session = requests.session()
# One session instance per command line invocation since this tool only handles one operation at a time.
# This is used throughout and allows for the request_mock library to be injected


def guid(guid):
    """ verifies GUID is in a valid format. helper function for argparse. """

    # GUID is a string that needs to be 32 characters
    if len(guid) != 32:
        raise argparse.ArgumentTypeError("GUID needs to be 32 characters")

    # GUID is all uppercase hexadecimal digits [0-9A-F]
    if not all([x in string.hexdigits.upper() for x in guid]):
        raise argparse.ArgumentTypeError("GUID is not a upper-case hexadecimal number")
    return guid


def future_time(epoch_time):
    """ verifies that the time (seconds since epoch) is after the current time. helper function for argparse """

    if time.time() > int(epoch_time):
        raise argparse.ArgumentTypeError("Specified time is not in the future")
    return epoch_time


def url(endpoint):
    """ verifies that URL has a <scheme>:// """

    # use the argparse.utils library to parse the URL
    if urlparse(endpoint).scheme == '':
        raise argparse.ArgumentTypeError("HTTP scheme needs to be provided, e.g. https://<host> or http://<host>")
    return endpoint


def add_expire(parser, required=False):
    """ helper function that adds --expire option to an argparse parser

    Keyword arguments:
    parser -- an instance of argparse.ArgumentParser
    required -- whether '--expire' is required, defaults to False
    """
    parser.add_argument('-e', '--expire', help='expire for guid', required=required, type=future_time)


def add_user(parser, required=False):
    """ helper function that adds --user option to an argparse parser

    Keyword arguments:
    parser -- an instance of argparse.ArgumentParser
    required -- whether '--user' is required, defaults to False
    """
    parser.add_argument('-u', '--user', help='user', required=required)


def add_guid(parser, required=False):
    """ helper function that adds --guid option to an argparse parser

    Keyword arguments:
    parser -- an instance of argparse.ArgumentParser
    required -- whether '--guid' is required, defaults to False
    """
    parser.add_argument('-g', '--guid', help='guid', required=required, type=guid)


def add_common_args(parser):
    """ helper function that adds options common to all sub-commands to an argparse parser

    Keyword arguments:
    parser -- an instance of argparse.ArgumentParser
    """

    # this is a spot to add --debug
    parser.add_argument('--url', help="endpoint URL", required=True, type=url)


def handle_response(request_func):
    """ decorator that handles HTTP Response, displaying info on success or failure.

    Keyword args:
    request_func -- a function that takes in argparse args, connects to a HTTP server, returns a HTTP response
    :returns wrapper function
    """

    def wrapper(args):
        r = request_func(args)
        try:
            r.raise_for_status()
            # this simply raises an exception for any HTTP error code (4xx or 5xx)
        except requests.exceptions.RequestException as e:
            print(e)
            # consider sys.exit(1) instead
        else:
            # prints the JSON output, consider a generic function that parses the returned JSON
            print(r.text)
            print("Success")
            # consider sys.exit(0) instead
    return wrapper


@handle_response
def create_request(args):
    """ handles the two CREATE GUID API cases """

    if args.guid is None:
        # If no GUID is specified, the server generates one. The expire option is ignored.
        # Consider throwing an error if expire is specified.
        body = json.dumps({"user": args.user})
        response = session.post(args.url + "/guid", data=body)
    else:
        # GUID is specified and this updates the expire time for the GUID
        body = json.dumps({"user": args.user, "expire": args.expire})
        response = session.post(args.url + "/guid/%s" % args.guid, data=body)
    return response


@handle_response
def read_request(args):
    """ handles the READ GUID API case """

    response = session.get(args.url + "/guid/%s" % args.guid)
    return response


@handle_response
def update_request(args):
    """ handles the UPDATE GUID API case """

    response = session.post(args.url + "/guid/%s" % args.guid, data=json.dumps({"expire": args.expire}))
    return response


@handle_response
def delete_request(args):
    """ handles the DELETE GUID API case """

    response = session.delete(args.url + "/guid/%s" % args.guid)
    return response


def main():
    parser = argparse.ArgumentParser(description='GUID client')
    parser.add_argument('--version', action='version', version=' '.join(['%(prog)s', __version__]))
    # string.join is faster than string concatenation via '+'

    subparsers = parser.add_subparsers(help='\'[sub-command] -h\' for further help on listed sub-commands')
    # create subparsers for each API call
    # use the helper functions to specify which arguments are required for each API call

    parser_create = subparsers.add_parser('create', help='create a GUID')
    add_expire(parser=parser_create)
    add_user(parser=parser_create, required=True)
    add_guid(parser=parser_create)
    add_common_args(parser=parser_create)
    parser_create.set_defaults(func=create_request)
    # this lets us call 'func' later to invoke the handler for each API call

    parser_read = subparsers.add_parser('read', help='read a GUID')
    add_guid(parser=parser_read, required=True)
    add_common_args(parser=parser_read)
    parser_read.set_defaults(func=read_request)

    parser_update = subparsers.add_parser('update', help='update a GUID')
    add_guid(parser=parser_update, required=True)
    add_expire(parser=parser_update, required=True)
    add_common_args(parser=parser_update)
    parser_update.set_defaults(func=update_request)

    parser_delete = subparsers.add_parser('delete', help='delete a GUID')
    add_guid(parser=parser_delete, required=True)
    add_common_args(parser=parser_delete)
    parser_delete.set_defaults(func=delete_request)

    parsed = parser.parse_args()
    if parsed.url.startswith("mock://"):
        # if there is a mock:// URL, we simulate the server so that the client
        # can be demoed and tested
        mock_server()
    parsed.func(parsed)


def mock_server():
    """ creates a mock server that handles API requests and allows for testing of HTTP error codes. """
    import requests_mock
    adapter = requests_mock.Adapter()
    session.mount('mock', adapter)
    # inject mock server into all future HTTP requests

    def read_callback(req, context):
        # dynamically mocks READ calls, returns the passed-in GUID in the JSON response

        guid = req.path[6:]  # assumes URI path is /guid/<guid>
        if guid[0] == "9":
            # if the first character of the guid is 9, fake a HTTP server error code
            context.status_code = 503
            context.reason = "mock server error test"
        if guid[0] == "8":
            # if the first character of the guid is 8, fake a HTTP client error code
            context.status_code = 404
            context.reason = "mock client error test"
        # generate JSON output regardless of error code.
        return json.dumps({"guid": guid, "expire": "1234123123123", "user": "foo"})

    def create_update_callback(req, context):
        # dynamically mocks CREATE/UPDATE calls, returns the passed-in GUID, USER, and EXPIRE
        # in the JSON response

        guid = "77777777777777"
        if len(req.path) > 5:
            guid = req.path[6:]  # assumes URI path is /guid/<guid>
        body = json.loads(req.text)
        response = body
        # CREATE and UPDATE returns EXPIRE, USER, and GUID in all calls
        if "expire" not in body:
            response['expire'] = "999999999999"  # provide fake if not specified in request
        if "user" not in body:
            response['user'] = "mock generated"  # provide fake if not specified in request
        response['guid'] = guid
        if guid[0] == "9":
            # if the first character of the guid is 9, fake a HTTP server error code

            context.status_code = 503
            context.reason = "mock server error test"
        if guid[0] == "8":
            # if the first character of the guid is 8, fake a HTTP client error code

            context.status_code = 404
            context.reason = "mock client error test"
        return json.dumps(response)

    def delete_callback(req, context):
        guid = req.path[6:]  # assumes URI path is /guid/<guid>
        if guid[0] == "9":
            # if the first character of the guid is 9, fake a HTTP server error code
            context.status_code = 503
            context.reason = "mock server error test"
        if guid[0] == "8":
            # if the first character of the guid is 8, fake a HTTP client error code
            context.status_code = 404
            context.reason = "mock client error test"
        # delete generates no output
        return ""

    mock_re = re.compile('mock://test.net/guid')  # assumes mock://test.net is passed in on CLI
    adapter.register_uri('GET', mock_re, text=read_callback)
    adapter.register_uri('POST', mock_re, text=create_update_callback)
    adapter.register_uri('DELETE', mock_re, text=delete_callback)

if __name__ == '__main__':
    main()
