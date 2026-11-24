# Resolve Desk

[Live demo on GitHub Pages](https://kowshikreddy099.github.io/resolve-desk/)

An automatic complaint resolver with 33 fictional scenarios. Choose a scenario, select **Use example**, then **Resolve complaint**. Each case includes a response, action reference where applicable, history and a downloadable JSON report.

The GitHub Pages edition processes complaints in your browser and saves them locally. The Python edition uses SQLite. All credits, exchanges and delivery actions are simulations.

## Local development

Run `python launch.py` with Python 3.9 or later. Run `python -m unittest -v` for backend tests.

## GitHub Pages

Run `python build_pages.py` after editing the interface or Python rules. Publish the main branch's docs directory using GitHub Pages.
