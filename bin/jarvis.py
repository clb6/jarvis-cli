import os, subprocess, argparse
from datetime import datetime


if "__main__" == __name__:
    parser = argparse.ArgumentParser(description='Jarvis is used for personal information management')

    subparsers = parser.add_subparsers(help='Actions for Jarvis',
            dest='action_name')
    parser_new = subparsers.add_parser('new', help='Create an information element')
    subparsers_new = parser_new.add_subparsers(help='Types of new information element',
            dest='element_type')
    parser_new_log = subparsers_new.add_parser('log', help='Create a new log entry')
    parser_new_tag = subparsers_new.add_parser('tag', help='Create a new tag element')
    parser_new_tag.add_argument('tag_name', help='Tag name')

    args = parser.parse_args()

    # NOTE: Argparse should filter and validate and ensure that only the known
    # choices get through to this point.
    # UPDATE: There is a case where the subsubparser allows for Nones to slip
    # through. The required flag doesn't seem to be reinforced so the following
    # is acceptable to Argparse which sucks for me:
    #   jarvis.py new

    if args.action_name == 'new':
        env_dir_jarvis_root = os.environ['JARVIS_DIR_ROOT']
        env_author = os.environ['JARVIS_AUTHOR']
        env_version = "0.1.0"

        created = datetime.utcnow().replace(microsecond=0)

        def create_stub_file(subdir_name, filename):
            dir_target = "{0}/{1}".format(env_dir_jarvis_root, subdir_name)

            filepath = "{0}/{1}.md".format(dir_target, filename)

            with open(filepath, 'w') as f:
                f.write("Author: {0}\n".format(env_author))
                f.write("Created: {0}\n".format(created.isoformat()))
                f.write("Version: {0}\n".format(env_version))
                f.write("Tags: \n")

            return filepath

        if args.element_type == 'log':
            # datetime.fromtimestamp(0) is not Unix epoch and returns
            # 1969-12-31 19:00 instead.
            epoch = datetime(1970, 1, 1)

            filepath = create_stub_file('LogEntries',
                int((created - epoch).total_seconds()))
        elif args.element_type == 'tag':
            filepath = create_stub_file('Tags', args.tag_name)
            print("TAG")
        else:
            raise NotImplementedError("Unknown information type: {0}"
                    .format(args.element_type))

        if filepath:
            subprocess.call(["vim", filepath])
            print("Created: {0}".format(filepath))
        else:
            print("Failed to create new information element")
