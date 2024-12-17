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

import sphinx_book_theme

html_theme_path = [sphinx_book_theme.get_html_theme_path()]
html_theme = 'sphinx_book_theme'
html_theme_options = {
    "repository_url": "https://github.com/btx0424/OmniDrones",
    "use_repository_button": True,
}

html_static_path = ['_static']

# Mock out modules that are not available on RTD
autodoc_mock_imports = [
    "numpy",
    "matplotlib",
    "scipy",
    "tqdm",
    "toml",
    "yaml",
    "opencv-python",
    "dv_processing"
]
