import os, subprocess, argparse
from datetime import datetime


if "__main__" == __name__:
    parser = argparse.ArgumentParser(description='Jarvis is used for personal information management')

    subparsers = parser.add_subparsers(help='Actions for Jarvis',
            dest='action_name')
    parser_create = subparsers.add_parser('new', help='Create an information element')
    parser_create.add_argument('type', choices=['entry', 'tag'],
            help='Information element type - required')

    args = parser.parse_args()

    # NOTE: Argparse should filter and validate and ensure that only the known
    # choices get through to this point.

    if args.action_name == 'new':
        env_dir_jarvis_root = os.environ['JARVIS_DIR_ROOT']
        env_author = os.environ['JARVIS_AUTHOR']
        env_version = "0.1.0"

        created = datetime.utcnow().replace(microsecond=0)

        def write_metadata(f):
            f.write("Author: {0}\n".format(env_author))
            f.write("Created: {0}\n".format(created.isoformat()))
            f.write("Version: {0}\n".format(env_version))
            f.write("Tags: \n")

        if args.type == 'entry':
            dir_jarvis_logs = "{0}/LogEntries".format(env_dir_jarvis_root)

            # datetime.fromtimestamp(0) is not Unix epoch and returns
            # 1969-12-31 19:00 instead.
            epoch = datetime(1970, 1, 1)

            filepath = "{0}/{1}.md".format(dir_jarvis_logs,
                    int((created - epoch).total_seconds()))

            with open(filepath, 'w') as f:
                write_metadata(f)

        subprocess.call(["vim", filepath])
        print("Created: {0}".format(filepath))
    else:
        print('DOH')
