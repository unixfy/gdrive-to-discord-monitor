# gdrive-to-discord-monitor
Monitors GDrive files by polling the Drive API then notifies Discord users on change. Designed to be run serverless.

## Why polling?

The interesting caveat with Drive's push mechanism is that the "watch" can only last 1 week at maximum. That means we need to somehow schedule a task to create new "watches" every week, update our function, and make sure there are no other "watches" existing. This is a lot of work, and it's easier to just poll in this case - particularly when the Drive API's rate limits are so high.
