# example template
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

## import some packages
import shelve

# Add tests directory to Python path

from tests.test_tools import load, save


def example_template_main():
    # no docstring
    # do something

    # optional: input
    input_data = load()

    # step 1: open a shelve
    shelve.open("example_template.shelve")

    # step 2: delete the shelve
    shelve.close()

    # step 3: result 
    result = {
        'shelve': 'example_template.shelve'
    }

    # optional: output
    save(result)


if __name__ == "__main__":
    example_template_main()