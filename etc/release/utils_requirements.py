#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others. All rights reserved.
# http://nexb.com and https://github.com/nexB/scancode-toolkit/
# The ScanCode software is licensed under the Apache License version 2.0.
# ScanCode is a trademark of nexB Inc.
#
# You may not use this software except in compliance with the License.
# You may obtain a copy of the License at: http://apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
#  ScanCode is a free software code scanning tool from nexB Inc. and others.
#  Visit https://github.com/nexB/scancode-toolkit/ for support and download.

import subprocess

"""
Utilities to manage requirements files and call pip.
NOTE: this should use ONLY the standard library and not import anything else.
"""


def load_requirements(requirements_file='requirements.txt', force_pinned=True):
    """
    Yield package (name, version) tuples for each requirement in a `requirement`
    file. Every requirement versions must be pinned if `force_pinned` is True.
    Otherwise un-pinned requirements are returned with a None version
    """
    with open(requirements_file) as reqs:
        req_lines = reqs.read().splitlines(False)
    return get_required_name_versions(req_lines, force_pinned)


def get_required_name_versions(requirement_lines, force_pinned=True):
    """
    Yield required (name, version) tuples given a`requirement_lines` iterable of
    requirement text lines. Every requirement versions must be pinned if
    `force_pinned` is True. Otherwise un-pinned requirements are returned with a
    None version
    """
    for req_line in requirement_lines:
        req_line = req_line.strip()
        if not req_line or req_line.startswith('#'):
            continue
        if '==' not in req_line and force_pinned:
            raise Exception(f'Requirement version is not pinned: {req_line}')
            name = req_line
            version = None
        else:
            name, _, version = req_line.partition('==')
            name = name.lower().strip()
            version = version.lower().strip()
        yield name, version


def get_requirements_from_setup_cfg(setup_cfg, extra=None):
    """
    Return a mapping of {type of requirement: list of requirements lines}
     extracted from a `setup_cfg` file *_requires sections.
    """
    import configparser
    config = configparser.ConfigParser()
    with open(setup_cfg) as cfg:
        config.read(cfg)

    requirements = {}
    install_requires = config.get('options', 'install_requires', fallback='')
    requirements['install_requires'] = parse_requires(install_requires)

    setup_requires = config.get('options', 'setup_requires', fallback='')
    requirements['setup_requires'] = parse_requires(setup_requires)

    extras_require = config.get('options', 'extras_require', fallback=[])
    for extra in extras_require:
        exreq = config.get('options.extras_require', extra, fallback='')
        requirements[f'extras_require:{extra}'] = parse_requires(exreq)

    return requirements


def parse_requires(requires):
    """
    Return a list of requirement lines extracted from the `requires` text from
    a setup.cfg *_requires section such as the "install_requires" section.
    """
    requires = [c for c in requires.splitlines(False) if c]
    if not requires:
        return []

    requires = [''.join(r.split()) for r in requires if r and r.strip()]
    return sorted(requires)


def lock_requirements(requirements_file='requirements.txt'):
    """
    Freeze and lock current installed requirements and save this to the
    `requirements_file` requirements file.
    """
    with open(requirements_file, 'w') as fo:
        fo.write(get_installed_reqs())


def lock_dev_requirements(
    dev_requirements_file='requirements-dev.txt',
    main_requirements_file='requirements.txt',
):
    """
    Freeze and lock current installed development-only requirements and save
    this to the `dev_requirements_file` requirements file. Development-only is
    achieved by subtracting requirements from the `main_requirements_file`
    requirements file from the current requirements using package names (and
    ignoring versions).
    """
    main_names = {n for n, _v in load_requirements(main_requirements_file)}
    all_reqs = get_installed_reqs().splitlines(False)
    all_reqs = get_required_name_versions(all_reqs)
    dev_only_reqs = {n: v for n, v in all_reqs if n not in main_names}
    new_reqs = '\n'.join(f'{n}=={v}' for n, v in sorted(dev_only_reqs.items()))
    with open(dev_requirements_file, 'w') as fo:
        fo.write(new_reqs)


def get_installed_reqs():
    """
    Return the installed requirements as a text.
    """
    # Do not skip these packages in the output: wheel, distribute, setuptools, pip
    args = ['pip', 'freeze', '--all', '--exclude-editable']
    return subprocess.check_output(args, encoding='utf-8')
