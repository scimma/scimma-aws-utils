import logging
import re
import xml.etree.ElementTree as ET
from base64 import b64decode, b64encode
from datetime import datetime
from random import randrange

from bs4 import BeautifulSoup

SCIMMA_PROXY_SSO = "https://federation-proxy.scimma.org/cilogon/sso/post"
LOGGER = logging.getLogger(__name__)


def login_aws_via_idp(session, username, password, entity_id):
    """ Get a SAML assertion and set of AWS roles which can be assumed with the SAML assertion. """
    LOGGER.info("Looking up your IdP")
    idp_url, idp_form = get_idp_login_form(
        session, username, password, entity_id)

    LOGGER.info("Logging in to %s", idp_url)
    idp_response = session.post(idp_url, data=idp_form)
    idp_response.raise_for_status()

    LOGGER.info("Parsing response and presenting assertion to CILogon")
    cilogon_url, payload = parse_idp_login_response(idp_response.text)
    scimma_saml_proxy_response = session.post(cilogon_url, data=payload)
    scimma_saml_proxy_response.raise_for_status()

    LOGGER.info("Login complete, extracting credentials")
    assertion = parse_scimma_sample_response(scimma_saml_proxy_response.text)
    roles = parse_scimma_aws_assertion(assertion)
    return assertion, roles


def get_idp_login_form(session, username, password, entity_id):
    url, payload = get_idp_discovery_form(session)
    payload["providerId"] = entity_id
    idp_form_response = session.post(url, data=payload, verify=True)
    idp_form_response.raise_for_status()
    idp_form = populate_idp_form(idp_form_response.text, username, password)
    return (idp_form_response.url, idp_form)


def get_idp_discovery_form(session):
    """Make a SAML auth request, follow the redirects, and return a CILogon IdP
    discovery form along with the URL to send it to.

    Uses the provided requests Session, which should follow redirects.
    """
    cilogon_form_response = post_authn_request(session)
    cilogon_form_response.raise_for_status()
    form_contents = parse_lxml_form(cilogon_form_response.text)
    return (cilogon_form_response.url, form_contents)


def parse_lxml_form(text):
    """ Parse lxml form into a dictionary of name:value based on the 'input' tags in text"""
    soup = BeautifulSoup(text, features="lxml")
    form = {}
    for inputtag in soup.find_all(re.compile("(INPUT|input)")):
        name = inputtag.get("name", "")
        value = inputtag.get("value", "")
        form[name] = value
    return form


def post_authn_request(session):
    """ Post a SAML authentication request to the SCIMMA SAML Proxy IdP.

    Uses the provided requests Session, which should follow redirects.
    """
    req = build_authn_request()
    return session.post(SCIMMA_PROXY_SSO, data={"SAMLRequest": req}, verify=True)


def build_authn_request():
    message_id = "_%030x" % randrange(16**30)
    timestamp = datetime.now().replace(microsecond=0).isoformat() + "Z"
    authn_request = f"""
<samlp:AuthnRequest
  xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
  xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
  AssertionConsumerServiceURL="https://signin.aws.amazon.com/saml"
  Destination="{SCIMMA_PROXY_SSO}"
  ID="{message_id}"
  IssueInstant="{timestamp}"
  ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
  Version="2.0">
  <saml:Issuer>urn:amazon:webservices</saml:Issuer>
    <samlp:NameIDPolicy AllowCreate="1" />
</samlp:AuthnRequest>

    """.encode()
    authn_base64 = b64encode(authn_request).decode("utf-8")
    return authn_base64


def populate_idp_form(form_text, username, password):
    """Try to populate an lxml login form. Make educated guesses on the username
    and password field names."""
    form = parse_lxml_form(form_text)
    result = {}
    for key, value in form.items():
        if "user" in key.lower():
            result[key] = username
        elif "email" in key.lower():
            result[key] = username
        elif "pass" in key.lower():
            result[key] = password
        else:
            result[key] = value
    # Shibboleth IdPs will need to include this field.
    result["_eventId_proceed"] = ""

    return result


def parse_idp_login_response(text):
    # Decode the response from the authenticating IdP and extract the SAML
    # assertion
    soup = BeautifulSoup(text, features="lxml")
    assertion = ''

    for inputtag in soup.find_all('input'):
        if (inputtag.get('name') == 'SAMLResponse'):
            assertion = inputtag.get('value')

        if (inputtag.get('name') == 'RelayState'):
            relay_state = inputtag.get('value')
    if assertion == "":
        raise ValueError("Response did not contain a valid SAML assertion")

    # Parse the returned payload to find the AssertionConsumerService URL
    # for the CILogon SP to which we will POST the SAML Response. Since CILogon
    # uses multiple SP ACS URLs we do not hardcode this.
    cilogon_sp_acs_url = soup.find('form').get('action')
    payload = {
        "SAMLResponse": assertion,
        "RelayState": relay_state,
    }
    return (cilogon_sp_acs_url, payload)


def parse_scimma_sample_response(text):
    """Extract the SAML Response assertion from from a CILogon SAML Proxy response. """
    soup = BeautifulSoup(text, features="lxml")
    assertion = ''

    for inputtag in soup.find_all('input'):
        if (inputtag.get('name') == 'SAMLResponse'):
            assertion = inputtag.get('value')
    return assertion


def parse_scimma_aws_assertion(assertion):
    """ Decode a SAML assertion and extract the AWS Roles it grants."""
    attr_element = '{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'
    attr_value_element = '{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'
    role_attribute_name = 'https://aws.amazon.com/SAML/Attributes/Role'
    aws_roles = []
    root = ET.fromstring(b64decode(assertion))
    for saml2attribute in root.iter(attr_element):
        if (saml2attribute.get('Name') == role_attribute_name):
            for saml2attributevalue in saml2attribute.iter(attr_value_element):
                aws_roles.append(saml2attributevalue.text)
    return aws_roles
