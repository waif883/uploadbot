# Upload Bot
Automatically upload audio to mixcloud. 

## Background

WAIF archives its programs internally. This tool uploads the internal archives to Mixcloud as the archive files are created.

The Upload Bot is a server that periodically checks for new files once they are populated in the `ARCHIVE_DIRECTORY` set in the configuration file. The audio recorder program will create a new audio file every hour and write into it until for one hour. This is important to know: once a file has been created in the `ARCHIVE_DIRECTORY` by the recorder, more time must elapse before that file has been filled. 

### Secrets.json
This program requires a `secrets.json` to be populated with access tokens necessary for remote services:
```json
{
    "MIXCLOUD": {
        "CLIENT_ID": "...",
        "CLIENT_SECRET": "...",
        "OATH_TOKEN": "...",
        "REDIRECT_URI": "www.waifradio.org",
        "ACCESS_TOKEN": "..."
    },
    "AIRTABLE": {
        "ACCESS_TOKEN": "...",
        "BASE_ID": "..."
    }   
}
```
You must replace `"..."` with the actual tokens for each service.

### Config.json
This program requires a `config.json` to be populated with program settings:
```json
{
    "ARCHIVE_DIRECTORY": "...",
    "CHECK_FILE_DURATION_SECONDS": 300,
    "UPLOAD_WAIT_HOURS": 1,
    "PROGRAM_TIMER_DURATION_SECONDS": 604800,
    "PROGRAM_TABLE_FILE": "programs.pkl"
}
```
You must replace `"..."` with the actual archive directory.


### Running the Bot
Should be as simple as running:
```console
python uploadbot/main.py --secrets secrets.json --config config.json
```

to make an executable:
```console:
pyinstaller --onefile --name UploadBot.exe main.py
```