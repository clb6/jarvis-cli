import os
import click
from jarvis_cli import config
from jarvis_cli.exceptions import JarvisCliConfigError
from jarvis_cli.interactive import prompt_init_config
from jarvis_cli.commands import action_new, action_edit, action_show, action_list, \
    action_admin

@click.group()
@click.option('-e', '--environment', default="default",
        help="Path to Jarvis cli configuration file")
@click.option('--config-path', default=config.JARVIS_CLI_CONFIG_PATH,
            help="Path to Jarvis cli configuration file")
# This is sweet
@click.version_option()
@click.pass_context
def cli(ctx, environment, config_path):
    # Decided to put the configuration initialization here rather than making it
    # potentially two steps: 1. Get error for lack of config 2. Run some explicit
    # init command that gets executed only once anyways.
    while True:
        try:
            config_map = config.get_config_map(environment, config_path)
            ctx.obj = { "config_map": config_map, "config_path": config_path,
                    "connection": config.get_client_connection(config_map),
                    "environment": environment }
            break
        except JarvisCliConfigError as e:
            click.echo("Jarvis-cli has not been initialized. Let's initialize now.")
            # Use the default snapshots dir because intermediaries created. If
            # not used, so what
            if not os.path.exists(config.JARVIS_CLI_DEFAULT_SNAPSHOTS_DIR):
                os.makedirs(config.JARVIS_CLI_DEFAULT_SNAPSHOTS_DIR)
            prompt_init_config(environment, config_path)

cli.add_command(action_new.do_action_new)
cli.add_command(action_edit.do_action_edit)
cli.add_command(action_show.do_action_show)
cli.add_command(action_list.do_action_list)
cli.add_command(action_admin.do_action_admin)
