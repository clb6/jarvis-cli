# Jarvis

Jarvis is a personal information management project.  It is a tool to help collect log entries and organize those log entries by tags.  The tags are not just left as metadata but also first-class entities as well.  The idea is that the log entries build up to ideas, concepts, and things which are tags.

## Setup

Jarvis requires the following environmental variables to be configured:

Variable Name | Description
--- | ---
JARVIS_DIR_ROOT | The full path to the root directory of where all the content will be written to
JARVIS_AUTHOR | The author of the content

In addition, the codebase uses the [`webbrowser`](https://docs.python.org/3/library/webbrowser.html) Python module which in turn on Unix machines uses the `xdg` tools to perform the launching of files.  If you wish to open the markdown files in your default browser because it has a nice markdown previewing extension, please change the **mimeapps.list** file to map the markdown mime type to the appropriate application like so:

```
[Added Associations]
text/x-markdown=chromium-browser.desktop
```

The full documentation on mimeapps.list can be found [here](http://standards.freedesktop.org/mime-apps-spec/mime-apps-spec-1.0.html).  The mimeapps.list can probably be found in your home directory `~/.local/share/applications/`.
