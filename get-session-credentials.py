import boto3
import os
from shutil import move
from botocore.exceptions import ClientError


creds = os.path.expanduser('~/.aws/credentials')
creds_bak = os.path.expanduser('~/.aws/credentials.python.backup')

# move backup credentials file if it exists
if os.path.isfile(creds_bak):
    move(creds_bak, creds)

# get username
username = input('Input your AWS Username: ')

if len(username) < 1:
    print('Username cannot be empty! Exiting...')
    exit(1)

# instantiate client and get device ARN
try:
    iam_client = boto3.client('iam')
    iam_response = iam_client.list_mfa_devices(UserName=username)
    mfa_arn = iam_response['MFADevices'][0]['SerialNumber']
except ClientError as ce:
    if ce.response['Error']['Code'] == 'NoSuchEntity':
        print('Username does not exist! Exiting...')
        exit(1)
    else:
        print('Unknown error. Exiting...')
        exit(1)

# get MFA code
mfa_code = input('Input your MFA Token: ')

if len(mfa_code) != 6:
    print('Incorrect MFA Length. Exiting...')
    exit(1)

# instantiate client and get session credentials and token
try:
    sts_client = boto3.client('sts')
    sts_response = sts_client.get_session_token(SerialNumber=mfa_arn, TokenCode=mfa_code)
    print('Session Token successful!')

except ClientError as ce:
    if ce.response['Error']['Code'] == 'AccessDenied':
        print('Incorrect MFA Code. Exiting...')
        exit(1)
    else:
        print('Unknown error. Exiting...')

# backup credentials file and write new session token credentials
move(creds, creds_bak)

# write new credentials file
credfile = open(creds, 'w')
credfile.write('[default]\n' +
               'aws_access_key_id = {}\n'.format(sts_response['Credentials']['AccessKeyId']) +
               'aws_secret_access_key = {}\n'.format(sts_response['Credentials']['SecretAccessKey']) +
               'aws_session_token = {}'.format(sts_response['Credentials']['SessionToken']))
credfile.close()
