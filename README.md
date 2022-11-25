# L0-fetcher
L0-fetcher syncs files from SFTP to AWS Buckets automatically by running [rclone](https://rclone.org/) wrapped in a scheduled lambda function.

# Build rclone
The lambda requires a lambda layer with [rclone](https://rclone.org/) before deploying.
To create one, first build locally by running
```
make build
```
Then upload the `.zip` archive as a Lambda layer and take note of its ARN.

# Deploy
1. Make sure your aws credentials are set up properly
2. Put an rclone config in AWS parameter store. The easiest way is by running `rclone config` locally and setting up remotes for SFTP and S3, then copying the contents of the file (default location is `/home/{user}/.config/rclone/rclone.conf`) to a parameter store __`SecureString`__ named __`/rclone/l0-fetcher`__ (this name can be changed in `app.py`). Note that the remotes __must__ be named `[FTP]` and `[S3]`.
 Here's an example of a config file:
```
[FTP]
type = sftp
pass = encrypted-password
host = host.sftp.com
user = user-name

[S3]
type = s3
provider = AWS
access_key_id = encrypted-key-id
secret_access_key = encrypted-access_key
region = eu-north-1
```

3. Run `cdk deploy`
