Python Documentation Workflow
=============================

This is an [Alfred v2](http://www.alfredapp.com) workflow to search the online Python [documentation](http://docs.python.org). It loosely emulates the behavior of the (javascript-based) `Sphinx` search function of the site.

Installation
-----------

[Download v1.0](https://github.com/RuiPereira/alfred-python-documentation/raw/v1.0/Python%20Documentation.alfredworkflow) and import into Alfred v2.

Usage
-----

- **`py [your search string]`** - search in the online Python documentation

    - the Python3 documentation is available with **`py3`**
    - selecting an item will open the corresponding documentation page, highlighting the search string
    - you can _quicklook_ the documentation without leaving Alfred with `⌘Y`

    ![Image](./screenshots/fdopen.png?raw=true)

- **modifier keys**

    - `cmd` - returns a succinct definition for _function_ entries from the local `pydoc` (Python 2 only)

    ![Image](./screenshots/fdopen_doc.png?raw=true)

    - `ctrl` - forcibly rebuild the local index

Features
--------

- tab-completion
- list module contents

![Image](./screenshots/os_pa.png?raw=true)

- fuzzy logic

![Image](./screenshots/os_path_sptxt.png?raw=true)

Acknowledgments
---------------
- the workflow includes `alfred.py`, from [alfred-python](https://github.com/nikipore/alfred-python)
- the [Python logo](http://www.python.org/community/logos/) is a trademark of the Python Software Foundation
