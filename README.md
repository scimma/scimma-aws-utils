# scimma-aws-utils #

This is a little tool for connecting to SCIMMA's AWS resources from the command
line using your institutional credentials. The main tool is a command-line
program called `scimma-aws`.

Run `scimma-aws setup` to install. You'll be prompted for some information.
After that, `scimma-aws login` will be used in the background to fetch
credentials automatically. You'll be able to use any AWS APIs without
re-entering credentials.

## Example ##

```
-> % pip install scimma-aws-utils
-> % scimma-aws setup

You'll need to provide your SAML IdP entity ID. Details on campus IdPs
including the SAML entity ID may be found at
https://incommon.org/federation/incommon-federation-entities/.

Some well-known IdP entity IDs:
  LIGO: https://login.ligo.org/idp/shibboleth
  University of Washington: urn:mace:incommon:washington.edu
Enter your IdP Entity ID:  urn:mace:incommon:washington.edu
Username you use to login to your IdP: swnelson
Password:
AWS Region to connect to [us-west-2]:
AWS credential profile name to use [default]:
Your configuration has been saved to /home/swnelson/.config/scimma-aws/config.
AWS configuration has been saved.

-> % aws sts get-caller-identity | jq
{
  "UserId": "AROAYQQCALM7SDS2266Y5:spencer.nelson",
  "Account": "<redacted>",
  "Arn": "arn:aws:sts::<redacted>:assumed-role/scimma_power_user/spencer.nelson"
}
```

## Prerequisites ##

You must be a member of the SCIMMA collaboration, with an account already
registered, and you must be in the DevOps group.

To make an account, follow the instructions [here](https://scimma.github.io/IAM/).

To get in the DevOps group, request membership [here](https://registry.scimma.org/registry/co_petitions/start/coef:4).

## Installation ##

`pip install scimma-aws-utils`

## One-time setup ##
Run `scimma-aws setup`. You'll be asked for an IdP Entity ID. You can look up
your entity ID from
[incommon](https://incommon.org/federation/incommon-federation-entities/). Find
your institution, click on it, and then click on "More technical info" in the
top corner of the window. Copy the "Entity ID" value verbatim.

You'll be prompted for your username and password. These should be whatever
credentials you use for your institution to log in.

Finally, you'll be prompted for an AWS region and profile name to use. The
defaults are right for most people. If you use multiple AWS accounts, you might
want to use a different profile name, though, like `"scimma"`. If you do, then
you'll just need to set the `AWS_PROFILE=scimma` environment variable before
doing any work with AWS APIs.

The setup program stores your username and password in
`~/.config/scimma-aws/config` by default.

Keep `scimma-aws` installed on your system and things should Just Work.

## Known Issues ##

### Terraform extra step ###
Because of a [longstanding
issue](https://github.com/terraform-providers/terraform-provider-aws/issues/6913)
with Terraform, you'll need to `export AWS_SDK_LOAD_CONFIG=1` for these
credentials to be usable by Terraform.
