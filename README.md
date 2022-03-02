# gdrive-to-discord-monitor
Monitors GDrive files by polling the Drive API then notifies Discord users on change. Designed to be run serverless.

## Why polling?

The interesting caveat with Drive's push mechanism is that the "watch" can only last 1 week at maximum. That means we need to somehow schedule a task to create new "watches" every week, update our function, and make sure there are no other "watches" existing. This is a lot of work, and it's easier to just poll in this case - particularly when the Drive API's rate limits are so high.

## IAM policy

Must allow the Lambda instance role to touch our SSM parameters. This IAM policy will allow access to all params:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ssm:PutParameter",
                "ssm:GetParameter"
            ],
            "Resource": "*"
        }
    ]
}
```

## Lambda function trigger

Create an EventBridge trigger with some cron expression (e.g. every 30 seconds) to automatically call the script.
