# PyXML
A basic python XML parser

## Introduction
This XML parser is produced as an easier to use / more intuitive alternative to the default XML parser included in Python.

## Features and Limitations
This XML parser is not intended to fully adhere to the XML specifications / recommendations. It will happily discard whitespaces and newlines without notice, if these characters are found at places where they are generally not important (such as indents before nested tags, etc.).

This approach does however improve the ease of use, as this allows all generally relevant values to be easily accessible by other applications without much background noise of "useless" characters. Furthermore, this method helps with adding new values to the XML structure, as the application does not have to deal with creating consistent spacing to make the final XML file look organised / readable.
