# -*- coding: UTF-8 -*-

import argparse
import os
import platform
import subprocess
import sys

from lib.build_cyfs_component import prepare_cyfs_components
from lib.common import MAC_CPUS, static_page_path, src_path, ts_sdk_path, cyfs_tools_path
from lib.git_patch import GitPatcher
from lib.ninja import build_browser
from lib.pack import make_installer
from lib.util import is_dir_exists

template = '''KALAMA_MAJOR=%s
KALAMA_MINOR=%s
KALAMA_NIGHTLY=%s
KALAMA_BUILD=%s
'''

IS_MAC = platform.system() == "Darwin"
DEFAULT_CPU = 'X86'


def _parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-name",
                        help="The project name.",
                        type=str,
                        required=True)
    parser.add_argument("--version",
                        help="The build version.",
                        type=str,
                        required=True)
    parser.add_argument("--target-cpu",
                        help="The target cpu, like X86 and ARM",
                        type=str,
                        default=DEFAULT_CPU,
                        required=False)
    parser.add_argument("--channel",
                        help="The kalama channel, like nightly and beta",
                        type=str,
                        default='nightly',
                        required=False)
    opt = parser.parse_args(args)

    assert opt.project_name.strip()
    assert opt.version.strip()
    if IS_MAC:
        assert opt.target_cpu.strip()
        assert opt.target_cpu in MAC_CPUS

    return opt


def check_requirements(root, target_cpu):
    _static_page_path = static_page_path(root, target_cpu)
    if not is_dir_exists(_static_page_path):
        sys.exit("kalama static page %s is not available, please check!" % _static_page_path)

    _ts_sdk_path = ts_sdk_path(root, target_cpu)
    if not is_dir_exists(_ts_sdk_path):
        sys.exit("cyfs ts sdk %s is not available, please check!" % _ts_sdk_path)

    _cyfs_tools_path = cyfs_tools_path(root, target_cpu)
    if not is_dir_exists(_cyfs_tools_path):
        sys.exit("cyfs ts sdk %s is not available, please check!" % _cyfs_tools_path)

    _chrome_src_path = os.path.join(src_path(root), "chrome")
    if not is_dir_exists(_chrome_src_path):
        sys.exit("chromium src %s is not available, please check!" % _chrome_src_path)

    check_chromium_branch(src_path(root))


def check_chromium_branch(src):
    try:
        cmd = ['git', 'symbolic-ref', '--short', 'HEAD']
        git_br = subprocess.check_output(cmd, cwd=src).decode('ascii').rstrip()
        if not git_br.startswith("kalama"):
            raise Exception("Current branch is not kalama branch ")
    except Exception as e:
        msg = "Check chromium code branch failed, error: %s" % e
        print(msg)
        sys.exit(msg)


def update_product_version(root, channel, version):
    channel_number = 1 if channel == 'beta' else 0
    product_version_file = os.path.join(root, "src", "chrome", "KALAMA_VERSION")
    with open(product_version_file, 'w') as f:
        f.write(template % ('1', '0', channel_number, version))


def main(args):
    root = os.path.normpath(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), os.pardir))

    opt = _parse_args(args)
    prepare_cyfs_components(root, opt.channel, opt.target_cpu, opt.version)
    check_requirements(root, opt.target_cpu)
    # patch
    GitPatcher.update(root)
    update_product_version(root, opt.channel, opt.version)

    # use chromium gn and ninja tool compile source code
    build_browser(src_path(root), opt.project_name, opt.target_cpu)

    # pack
    make_installer(root, opt.project_name, opt.version, opt.target_cpu, opt.channel)

    print("Build finished!!")


if __name__ == "__main__":
    try:
        print(str(sys.argv))
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.stderr.write("interrupted\n")
        sys.exit(1)
