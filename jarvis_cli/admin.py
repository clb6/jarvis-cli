import subprocess, os
from datetime import datetime
from jarvis_cli import config


def create_snapshot(environment):
    snapshot_filepath = "jarvis_snapshot_{0}_{1}.tar.gz".format(environment,
            datetime.utcnow().strftime("%Y%m%d%H%M%S"))
    snapshot_filepath =os.path.join(config.get_jarvis_snapshots_directory(environment),
            snapshot_filepath)

    data_dir = config.get_jarvis_data_directory(environment)
    data_top_dirname = os.path.dirname(data_dir)
    data_basename = os.path.basename(data_dir)

    cmd = ["tar", "-czf", snapshot_filepath, "-C", data_top_dirname, data_basename]

    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if cp.returncode == 0:
        return snapshot_filepath
    else:
        # Tarballing failed and there maybe a bad tarball so try to remove it
        try:
            os.remove(snapshot_filepath)
        except:
            pass

        print(cp.stdout)
