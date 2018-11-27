# PwdSync
Simple Password Manager with a cross platform command line interface.

It's still under development.

## Config file
PwdSync can be configured using the config file located at `~/.pwdsync/config.yml` on Linux or `%HOMEPATH%\Documents\pwdsync\config.yml` on Windows.

## Storage format
After decryption the file has this format:
```
{
    "history": [
        // unix_timestamp, pwd_entry_name, changed_key, changed_value
        [1237083, "my-app", "password", "abcNewPass"]
    ],
    "passwords": {
        "internet": {
            "twitter": {
                "name": "twitter",
                "username": "admin",
                "password": "adminpwd",
                "comment": "Here I choose an extremely good pwd!!!"
            }
        }
    }
}
```
