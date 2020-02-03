import jsii

from aws_cdk import core
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_iam as iam
from aws_cdk import aws_cognito as cognito


class ApiDynamoStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # The code that defines your stack goes here
        user_pool = cognito.UserPool(self, "UsersPool", sign_in_type=cognito.SignInType.USERNAME)
        cfn_user_pool: cognito.CfnUserPool = user_pool.node.default_child
        cfn_user_pool.policies = cognito.CfnUserPool.PoliciesProperty(
            password_policy=cognito.CfnUserPool.PasswordPolicyProperty(
                minimum_length=8,
                require_lowercase=False,
                require_numbers=False,
                require_symbols=False,
                require_uppercase=False
            )
        )

        user_pool_client = cognito.UserPoolClient(self, "PoolClient",
            user_pool=user_pool,
            enabled_auth_flows=[cognito.AuthFlow.ADMIN_NO_SRP, cognito.AuthFlow.USER_PASSWORD])

        table = dynamodb.Table(self, "TestTable", 
            partition_key=dynamodb.Attribute(
                name="name",
                type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.DESTROY,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES)

        statuses = {
            "200": ""
        }
        integration_responses = []

        for k,v in statuses.items():
            integration_responses.append(
                apigateway.IntegrationResponse(
                    status_code = k,
                    selection_pattern=v
                )
            )

        apigateway_role = iam.Role(self, "ApiGatewayRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com")
        )
        table.grant_read_write_data(apigateway_role)

        dynamo_integration = apigateway.AwsIntegration(
            proxy=False,
            service="dynamodb",
            integration_http_method="POST",
            action="PutItem",
            options=apigateway.IntegrationOptions(
                credentials_role=apigateway_role,
                request_templates={
                    "application/json": f"""{{
                        "TableName": "{table.table_name}",
                        "Item": {{
                            "name": {{
                                "S": "$input.path('$.name')"
                            }},
                            "id": {{
                                "S": "$context.requestId"
                            }},
                            "email": {{
                                "S": "$input.path('$.email')"
                            }},
                            "phone": {{
                                "S": "$input.path('$.phone')"
                            }},
                            "createTime": {{
                                "S": "$context.requestTime"
                            }}
                        }}
                    }}"""
                },
                integration_responses=integration_responses
            )
        )

        method_responses = []
        for k,v in statuses.items():
            method_responses.append(
                apigateway.MethodResponse(status_code = k)
            )
   
        api = apigateway.RestApi(self, "test-api")

        auth = apigateway.CfnAuthorizer(self, "testAuthorizer",
            rest_api_id=api.rest_api_id,
            identity_source="method.request.header.Authorization",
            provider_arns=[user_pool.user_pool_arn],
            type="COGNITO_USER_POOLS",
            name='TestCognitoAuthorizer'
        )

        post_method = api.root.add_method("POST", dynamo_integration, method_responses=method_responses)

        post_child: apigateway.CfnMethod = post_method.node.find_child('Resource')
        post_child.add_property_override('AuthorizationType', apigateway.AuthorizationType.COGNITO)
        post_child.add_property_override('AuthorizerId', { 'Ref': auth.logical_id })


