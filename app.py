#!/usr/bin/env python3

from aws_cdk import core

from api_dynamo.api_dynamo_stack import ApiDynamoStack


app = core.App()
ApiDynamoStack(app, "api-dynamo")

app.synth()
