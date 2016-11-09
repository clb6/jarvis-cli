# jarvis-cli

jarvis-cli is a Python command-line tool used to interact with the [jarvis-api](https://github.com/clb6/jarvis-api).

## Commands

* `admin` - jarvis-api administrative actions
* `edit` - edit existing events, log entries, or tags
* `list` - query and list events, log entries, or tags
* `new` - create new events, log entries, or tags
* `show` - display specified events, log entries, or tags

## Environment Variables

Variable Name | Description
------------- | -----------
EDITOR | Editor application to use

## Configuration File

A configuration file is required.  jarvis-cli assists in the generation of the configuration file when one does not already exist.

The configuration file is written to `$HOME/.jarvis/cli_config.ini`.

In the configuration file, each subsection is an *environment* and each environment has its own set of parameters.  Example:

```
[default]
api_url = http://your-jarvis-api.com/
```

The environment can be selected with the `--environment` command argument.  The `default` environment is the default environment and does not have to be specified.

### Configuration parameters

Parameter Name | Description
-------------- | -----------
author | Author name to use
api_url | jarvis-api URL
data_directory | Local jarvis-api data directory used to perform backups
snapshots_directory | Directory where the backup snapshots are stored

### Viewing Markdown

jarvis-cli uses the [`webbrowser`](https://docs.python.org/3/library/webbrowser.html) Python module.

#### On Unix machines

`webbrowser` uses `xdg` to perform the launching of files.  If you wish to open the markdown files in your default browser because you have installed a markdown previewing extension, change the **mimeapps.list** file to map the markdown mime type to the appropriate application like so:

```
[Added Associations]
text/x-markdown=chromium-browser.desktop
```

The full documentation on mimeapps.list can be found [here](http://standards.freedesktop.org/mime-apps-spec/mime-apps-spec-1.0.html).  The mimeapps.list can probably be found in your home directory `~/.local/share/applications/`.
