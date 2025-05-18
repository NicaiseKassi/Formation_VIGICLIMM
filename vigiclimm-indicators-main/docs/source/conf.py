# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'vigiclimm_indicators'
copyright = '2024, MFI'
author = 'MFI'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.napoleon',
    'sphinx_rtd_theme',
    'sphinxcontrib.mermaid',
    'sphinx.ext.todo',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    "sphinx.ext.doctest",
    'sphinx_click'
]

autosummary_generate = True
todo_include_todos = True

templates_path = ['_templates']
exclude_patterns = []


sphinxmermaid_mermaid_init = {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#BB2528',
    'primaryTextColor': '#fff',
    'primaryBorderColor': '#7C0000',
    'lineColor': '#F8B229',
    'secondaryColor': '#006100',
    'tertiaryColor': '#fff'
  }
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
