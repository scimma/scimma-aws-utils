# scimma-aws-utils #

This is a little tool for connecting to SCIMMA's AWS resources from the command
line using your institutional credentials. The main tool is a command-line
program called `scimma-aws`.

Run `scimma-aws setup` to install. You'll be prompted for some information.
After that, `scimma-aws login` will be used in the background to fetch
credentials automatically. You'll be able to use any AWS APIs without
re-entering credentials.

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
