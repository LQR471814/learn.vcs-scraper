del /q .\dist\*
py setup.py sdist
py -m twine upload dist/*