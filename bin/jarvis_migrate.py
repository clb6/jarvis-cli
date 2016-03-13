#!/usr/bin/env python
#
# Script migrates Jarvis data from previous version to latest version through the
# Jarvis API.

import os, re, json
import requests


def _convert_file_to_json(file_path):
    """
    Form a json representation of a log file.

    Example of return response:

    {
        "author": "John Doe",
        "created": "2015-12-12T16:22:41",
        "occurred": "2015-11-25T00:00:00",
        "version": "0.2.0",
        "tags": ["Weather", "HelloWorld"],
        "parent": "123456789",
        "todo": "Read *War and Peace*",
        "setting": "Finished reading *The Cat and the Hat* while watching a very
        orange sunset.",
        "body": "Today was a bright and sunny day!"
    }

    :param file_path: full path of the file
    :type file_path: string

    :return: json
    """
    with open(file_path, 'r') as f:
        (metadata, body) = f.read().split('\n\n', maxsplit=1)

        def parse_metadata(line):
            """
            :param line: line for metadata e.g. "Author: John Doe"
            :type line: string

            :return: (key string, value string)
            """
            m = re.search('^(\w*): (.*)', line)
            # Watch! Stripping trailing whitespace because for some reason
            # certain field values are showing whitespace.
            return m.group(1).lower(), m.group(2).strip()

        t = [ parse_metadata(line) for line in metadata.split('\n') ]

        response = dict(t)
        response['tags'] = response['tags'].split(', ')
        # Handle scenario when there are no tags which will return an empty
        # string. Also strip the unnecessary whitespaces.
        response['tags'] = [ tag.strip() for tag in response['tags'] if tag ]
        response['body'] = body
        return response


def migrate_resources(resource_type, version):
    dir_resources_to_migrate = os.path.join(os.environ['JARVIS_DIR_ROOT'],
            "{0}_v{1}".format(resource_type, version))
    print("Migrate {0}: {1}".format(resource_type.lower(),
        dir_resources_to_migrate))
    num_migrated = 0
    num_total = 0

    for resource_file in os.listdir(dir_resources_to_migrate):
        resource_path = os.path.join(dir_resources_to_migrate, resource_file)
        resource_to_migrate = _convert_file_to_json(resource_path)
        resource_name = resource_file.replace(".md", "")

        r = requests.put("http://localhost:3000/{0}/{1}/migrate" \
                .format(resource_type.lower(), resource_name), json=resource_to_migrate)

        if r.status_code == 200:
            print("OK: {0}".format(resource_name))
            num_migrated += 1
        elif r.status_code == 409:
            print("Conflict: {0}".format(resource_name))
        else:
            print("Error: {0}, {1}".format(resource_name, r.json()))
            print(json.dumps(resource_to_migrate))

        num_total += 1

    print("Done: {0}migrated/{1}total".format(num_migrated, num_total))


def migrate_log_entries(version):
    migrate_resources("LogEntries", version)

def migrate_tags(version):
    migrate_resources("Tags", version)


if "__main__" == __name__:
    version = 1
    migrate_tags(version)
    migrate_log_entries(version)
