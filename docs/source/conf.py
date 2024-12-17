import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

extensions = [
    'sphinx.ext.autodoc',
]

project = 'DVS detect whell position'
copyright = '2024, Fausto M. Lagos S.'
author = 'Fausto M. Lagos S. - piratax007'
release = '0.1.0'
master_doc = 'index'

html_theme = 'sphinx_rtd_theme'

html_context = {
    "display_github": True,
    "github_user": "piratax007",
    "github_repo": "Detect_wheel_position_DVS_Camera",
    "github_version": "main",
    "conf_py_path": "/source/",
}
