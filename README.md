# scimma-aws-utils #

This is a little tool for connecting to SCIMMA's AWS resource from the command
line using your institutional credentials.

## Prerequisites ##

You must be a member of the SCIMMA collaboration, with an account already
registered, and you must be in the DevOps group.

To make an account, follow the instructions [here](https://scimma.github.io/IAM/).y

To get in the DevOps group, request membership [here](https://registry.scimma.org/registry/co_petitions/start/coef:4).

## Installation ##

`pip install scimma-aws-utils`

## Usage ##

### First-time setup ###
Run `scimma-aws setup`. You'll be asked for an IdP Entity ID. You can look up
your entity ID from
[incommon](https://incommon.org/federation/incommon-federation-entities/). Find
your institution, click on it, and then click on "More technical info" in the
top corner of the window. Copy the "Entity ID" value verbatim.

You'll be prompted for your username and password. These should be whatever
credentials you use for your institution to log in.

Finally, you'll be prompted for an AWS region and profile name to use. The
defaults are right for most people.

The setup program stores your username and password in
`~/.config/scimma-aws/config` by default.

### Usage ###
To set up a terminal to be logged in, run `$(scimma-aws login --eval)`. This
will log in to your institution using your saved credentials, and then generate
AWS credentials. Finally, it outputs (to stdout) a command that can be evaluated
to set your AWS profile for the session.

Credentials last for an hour. After that, they must be renewed; you can do this
by running `scimma-aws login` again.
