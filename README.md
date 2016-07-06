# Jarvis

Jarvis is a personal information management project.  It is a tool to help collect log entries and organize those log entries by tags.  The tags are not just left as metadata but also first-class entities as well.  The idea is that the log entries build up to ideas, concepts, and things which are tags.

## Setup

### Environment Variables

Jarvis requires the following environmental variables to be configured:

Variable Name | Description
------------- | -----------
EDITOR | The editor application name

### Configuration File

A configuration file is required in the following directory path: `$HOME/.jarvis/cli_config.ini`.  Each subsection is an environment and the only environment required is `default`.  Example,

```
[default]
host = localhost
port = 3000
```

Configuration parameters include:

Parameter Name | Description
-------------- | -----------
author | Authors name used on log entries
host | Hostname of Jarvis-api to use
port | Port of Jarvis-api to use
data_directory | Data directory for the Jarvis-api - used for backing up
snapshots_directory | Snapshots directory where backups are stored

### Viewing Markdown

In addition, the codebase uses the [`webbrowser`](https://docs.python.org/3/library/webbrowser.html) Python module which in turn on Unix machines uses the `xdg` tools to perform the launching of files.  If you wish to open the markdown files in your default browser because it has a nice markdown previewing extension, please change the **mimeapps.list** file to map the markdown mime type to the appropriate application like so:

```
[Added Associations]
text/x-markdown=chromium-browser.desktop
```

The full documentation on mimeapps.list can be found [here](http://standards.freedesktop.org/mime-apps-spec/mime-apps-spec-1.0.html).  The mimeapps.list can probably be found in your home directory `~/.local/share/applications/`.

## Workflow

The goal to absorbing, to experiencing, to learning in life is to curate knowledge and perceptions on concepts and how they inter-relate.  The hypothesis is that curating concepts requires one to have one to many different experiences which are recorded via log entries.  The flow is to create log entries which are to be used for creating curated content.

### Log Entries

* Recordings on experiences
* Reflections on the digestion of information
* Notes on observations
* Thoughts on the universe

### Tags

People, places, things, concepts that best define what we experience or best describes what we are trying to capture.

