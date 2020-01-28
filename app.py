#!/usr/bin/env python3

import getpass

from aws_cdk import core

from api_dynamo.api_dynamo_stack import ApiDynamoStack


app = core.App()
core.Tag.add(app, 'owner', getpass.getuser())
ApiDynamoStack(app, f"{getpass.getuser()}-api-dynamo")

app.synth()
