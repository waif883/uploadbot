# Upload Bot
Automatically upload audio to mixcloud. 

## Installation
Requires a `secrets.json` to be populated with access tokens necessary for remote services:
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


## Running the Bot
Should be as simple as running:
```console
python main.py
```