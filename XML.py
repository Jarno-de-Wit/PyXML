"""
XML Parser / Editor / Creator
"""
import itertools as it

class XML():
    def __init__(self, name = "", database = None, attributes = None, tag_type = "auto"):
        self.name = name
        if database is not None:
            self.database = database
        else:
            self.database = []
        if attributes is not None:
            self.attributes = attributes
        else:
            self.attributes = {}
        self.type = tag_type

    @classmethod
    def XMLFile(cls, filepath = None):
        """
        Loads an XML structure from a given file path
        """
        if not filepath:
            return XML()
        else:
            with open(filepath, "r", encoding = "utf-8-sig") as file:
                data = file.readlines() #Readlines is preferred in this case to be able to easily remove the XML header info
        while data:
            if data[0][0:1] == "<":
                if data[0][1:2] == "?":
                    data.pop(0)
                elif data[0][1:2] == "!":
                    data.pop(0)
                else:
                    return cls.from_str("".join(data))
            else:
                data.pop(0)
        raise RuntimeError("Couldn't read XML File. Does the file contain a valid XML structure?")

    @classmethod
    def from_str(cls, data, return_trailing = False):
        """
        Loads an XML structure from a string

        data: string - string to be parsed to an XML structure.
        return_trailing: bool - determines whether the text after the parsed element should be returned.
        """
        self = cls() #Set up an XML object to return in the end

        #Find the header position ----------------------------------------------
        header_end = 0
        while True:
            header_end = data.find(">", header_end + 1) #Search for the ">" header ender, starting from the spot after the previous position.
            if header_end == -1:
                raise EOFError(f"Unclosed header tag")
            if not cls.__in_str(data, header_end): #If the ">" was not encased by double quotation marks, and thus was not part of a string / value:
                header_end += 1 #Move the index over by 1, so it ends using [:header_end] as an index also includes the ">" itself
                break #Break out of the while loop. The ">" has been found

        #Decode the header -----------------------------------------------------
        header_data = data[:header_end].removeprefix("<").removesuffix(">")

        if header_data[-1] == "/":
            self.type = "short"
            header_data = header_data.removesuffix("/") #Remove the trailing "/" if it exists (which would indicate a short tag)
        else:
            self.type == "long"
        header_data = header_data.split(" ", 1) #Split the header into: [0] The tag name; [1] The attribute list
        self.name = header_data[0] #Set the tag name
        if len(header_data) == 2: #If the tag contained any attributes:
            attributes = cls.__split_str(header_data[1]) #Split the header data at each " or ', to separate the attributes from their value
            for attr in attributes:
                self.attributes[attr[0].strip("= \t\n")] = cls.decode(attr[1]) #Set the attribute in the attributes list. For the attribute name, any leading/trailing spaces, and the "=" sign are removed. The data is left unchanged, as anything withing the '"' was part of the string anyway.
        if self.type == "short": #If the tag is of the short type, and thus consists only of a "header", return it now.
            if return_trailing: #If requested, also return all unused "trailing" data
                return self, data[header_end:]
            else:
                return self

        #Decode the body of the XML tag ----------------------------------------
        data = data[header_end:]
        data = data.lstrip(" \t\n")
        while index := data.find(f"</{self.name}>"): #While the next part in the data is not this data's own end tag, there must be another child in between:
            if index == -1:
                raise EOFError(f"No valid closing tag found for tag with name '{self.name}'")
            if tag_index := data.find("<"): #If the next part is text, and not an XML tag:
                child = cls.decode("\n".join(line.strip(" \t") for line in data[:tag_index].rstrip(" \t\n").split("\n")))
                data = data[tag_index:]
            else:
                child, data = cls.from_str(data, return_trailing = True)
            self.database.append(child) #Append the tag to the database
            data = data.lstrip(" \t\n") #Strip any spacing that was between two XML tags.

        #Remove the end tag from the data --------------------------------------
        data = data.removeprefix(f"</{self.name}>")

        #Return whatever data is necessary
        if return_trailing:
            return self, data
        else:
            return self

    def __getitem__(self, item):
        if item in self.attributes: #If the item is an attribute, return the attribute's value
            return self.attributes[item]
        elif type(item) == int: #Elif the item is an integer index, return the corresponding child
            return self.database[item]
        elif item in (itm.name for itm in self.database): #Elif the item is the name of any of the children, return the child.
            return self.database[[itm.name for itm in self.database].index(item)] #Find the index of the first item with the same name, and return the item at that index.
        else:
            raise KeyError(item)

    def __setitem__(self, item, value):
        if type(item) == int and item < len(self.database):
            self.database[item] = value
        else:
            self.attributes[item] = value

    def append(self, value):
        """
        Append a value (either a new XML tag, or a str) to the database
        """
        self.database.append(value)


    def keys(self):
        """
        Returns the list of all attribute names
        """
        keys = list(self.attributes.keys())
        return keys

    def __str__(self):
        return f"<XML object {self.name}>"

    def __repr__(self):
        return f"<XML object {self.name} with keys {self.keys()} and {len(self.database)} children>"

    def test_attr(self, attributes, values = None):
        """
        Tests if an XML object has the requested attributes, and if these attributes are set to the given values

        attributes: str / iterable - A (list of) attribute names that should be checked.
        values: NoneType / str / iterable - The respective values the attributes should have. Set to None to accept any value as correct.

        returns: Bool - True if criteria are met, False otherwise.
        """
        #Make sure the 'attributes' variable is an iterable containing attr names
        if isinstance(attributes, str) or not hasattr(attributes, "__iter__"):
            attributes = (str(attributes),)
        else:
            #Turn any iterable into a tuple to avoid issues with generator
            # expressions getting exhausted after a single use
            attributes = tuple(attributes)

        #Make sure the 'values' variable is an iterable containing values
        if isinstance(values, str) or not hasattr(values, "__iter__"):
            values = len(attributes) * (values,)

        #Test if all given attributes exist
        if all(attr in self.keys() for attr in attributes):
            #Test if all given attributes have the requested value (or the value is irrelevant (None))
            if all(self[attr] == val for attr, val in zip(attributes, values) if val is not None):
                return True
        #If any of the tests failed, return None
        return False

    def get_filtered(self, attribute, value = None, recursion_depth = -1, sort = True):
        """
        Returns the first item in the database, for which the value of "attribute" is equal to "value"

        If value is None, returns the first item that has the given attribute.

        Useful for example when there is a list of parts, each having an attribute "id", where you want to find a part with a specific id.
        """
        return next((tag for tag in self.iter_tags(recursion_depth, sort) if tag.test_attr(attribute, value)), None)

    def get_filtered_all(self, attribute, value = None, recursion_depth = -1, sort = True):
        """
        Returns all items in the database, for which the value of "attribute" is equal to "value"

        If value is None, returns all items that have the given attribute.
        Recursion depth determines up to how many levels deep the search should go. Set to < 0 for unlimited recursion.
        """
        return [tag for tag in self.iter_tags(recursion_depth, sort) if tag.test_attr(attribute, value)]

    def find(self, name, recursion_depth = -1, sort = True):
        """
        Returns the first tag which has the given tag.name
        """
        return next((tag for tag in self.iter_tags(recursion_depth, sort) if tag.name == name), None)

    def find_all(self, name, recursion_depth = -1, sort = True):
        """
        Returns all tags which have the given tag.name
        """
        return [tag for tag in self.iter_tags(recursion_depth, sort) if tag.name == name]

    def iter_database(self, recursion_depth = -1, sort = True, nested_tree = False):
        """
        Returns a tuple of all nested items, nested up to a depth of 'recursion_depth'

        If recursion_depth is < 0; recursion is unlimited.
        If sort is True, all items are returned sorted based on their nesting level. Else, all items are returned in a tree order.
        If nested_tree is True, will not return a flat tuple, but will instead return a (one level) nested tuple of all items, based on their nesting level. Requires sort to be True.
        """
        if sort and nested_tree:
            return (tuple(self.database),) + tuple(sum(tags, ()) for tags in it.zip_longest(*(tag.iter_database(recursion_depth - 1, True, True) for tag in self.database if isinstance(tag, XML)), fillvalue = ()) if tags) if recursion_depth else ()
        elif sort:
            #Simply flatten the nested_tree sorted list
            return sum(self.iter_database(recursion_depth, True, True), ())
        else:
            return sum(((tag,) + tag.iter_database(recursion_depth - 1, False) if isinstance(tag, XML) else (tag,) for tag in self.database), ()) if recursion_depth else ()

    def iter_tags(self, recursion_depth = -1, sort = True, nested_tree = False):
        """
        Returns a tuple of all nested tags, nested up to a depth of 'recursion_depth'

        If recursion_depth is < 0; recursion is unlimited.
        If sort is True, all items are returned sorted based on their nesting level. Else, all items are returned in a tree order.
        If nested_tree is True, will not return a flat tuple, but will instead return a (one level) nested tuple of all items, based on their nesting level. Requires sort to be True.
        """
        if sort == True and nested_tree == True:
            return tuple(tuple(tag for tag in branch if isinstance(tag, XML)) for branch in self.iter_database(recursion_depth, sort, nested_tree))
        else:
            return tuple(tag for tag in self.iter_database(recursion_depth, sort, nested_tree) if isinstance(tag, XML))

    @property
    def tags(self):
        """
        Returns all XML tags contained in the database
        """
        return tuple(tag for tag in self.database if isinstance(tag, XML))

    @property
    def max_depth(self):
        """
        Returns the maximum depth of any of the nested tags
        """
        if tags := self.tags:
            return 1 + max(child.max_depth for child in tags)
        else:
            return 0

    def copy(self, deepcopy = False):
        """
        Returns a copy of self

        deepcopy: bool - Determines whether nested tags should also be copied, or whether the original nested tag should be used in the new database. If false, a shallow copy will be performed.
        Note: deepcopy only applies to nested tags. The database / attributes will always be a separate object.
        """
        if deepcopy:
            return XML(self.name, [tag.copy(True) if isinstance(tag, XML) else tag for tag in self.database], self.attributes.copy(), self.type)
        else:
            return XML(self.name, self.database.copy(), self.attributes.copy(), self.type)

    def deepcopy(self):
        """
        Synonym for *.copy(True)
        """
        return self.copy(True)

    def reduce(self, recursion_depth = -1, reduce_multiline = True):
        """
        Tries to minimise the number of nested tags by turning tags which only contain a single string value into an attribute instead

        reduce_multiline: Bool - Determines whether multi-line text should be reduced as well.
        """
        if recursion_depth == 0:
            return
        for tag in self.tags:
            tag.reduce(recursion_depth - 1)
        tag_names = [tag.name for tag in self.tags]
        tag_count = len(self.database)
        for tag_num, tag in list(enumerate(self.database)):
            if not isinstance(tag, XML): # Make sure text is not compressed (because it can't be)
                continue
            # Checks:
            # Must contain only one items
            # Contained item must be string
            # String must not contain any newline
            # Tag name must not occur multiple times (prevent preferenatial treatment)
            # Tag name must not exist yet in attributes (prevent overwriting existing attributes)
            if len(tag.database) == 1 and isinstance(tag.database[0], str) and (not "\n" in tag.database[0] or reduce_multiline) and tag_names.count(tag.name) == 1 and not tag.name in self.attributes:
                self.attributes[tag.name] = tag.database[0]
                # Note: Reverse indexing used to circumvent index shift when removing items at the start
                self.database.pop(-tag_count + tag_num)

    def expand(self, recursion_depth = -1, force_expand = False):
        """
        Expands a tag into its long form, by turning all attributes to separate tags containing text instead

        force_expand: Bool - Determines whether the expansion should expand attributes if a nested tag with the same name already exists.
        """
        if recursion_depth == 0:
            return
        for tag in self.tags:
            tag.expand(recursion_depth - 1, force_expand)
        tag_names = [tag.name for tag in self.tags]
        for tag in list(self.attributes):
            if force_expand or tag not in tag_names:
                self.append(XML(tag, database = [self.attributes.pop(tag)]))

    def write(self, file, allow_compact = True, depth = 0):
        """
        Write the XML structure to a given file

        file: string / filepath - The path to the file the XML should be stored to.
        allow_compact: bool - Determines whether XML tags containing only a single text based database entry are allowed to be written as a single line tag, instead of taking up three lines.
        depth: int - The indentation (in '  ') the XML tag should have by default.
        """
        if not hasattr(file, "write"):
            with open(file, "w", encoding = "utf-8-sig") as f:
                f.write('<?xml version="1.0" encoding="utf-8"?>\n') #Write the XML header
                self.write(f, allow_compact, depth) #Write the contents of the tag(s) to the (now opened) file
        else:
            file.write(f"{depth * '  '}{self.header}")
            if  allow_compact and len(self.database) == 1 and not isinstance(self.database[0], XML):
                file.write(f"{self.encode(self.database[0])}")
            else:
                file.write("\n")
                for child in self.database:
                    if isinstance(child, XML):
                        child.write(file, allow_compact, depth + 1)
                    else:
                        file.write(f"{(depth + 1) * '  '}{self.encode(child.replace(chr(10), chr(10) + (depth + 1) * '  '))}\n")
                if self.type == "long" or (self.type == "auto" and self.database):
                    file.write(f"{depth * '  '}")
            if self.type == "long" or (self.type == "auto" and self.database):
                file.write(f"</{self.name}>\n")


    @property
    def header(self):
        """
        Builds the header string for writing the XML tag to a file
        """
        string = f"<{self.name}"
        for attr in self.attributes:
            value = str(self.attributes[attr]) #Turn the value into a string, without any " surrounding it.
            string = " ".join([string, f'{attr}="{self.encode(value)}"'])
        if self.type == "short" or (self.type == "auto" and not self.database): #If the tag is of the short type, add the "/" to the end to signify this.
            string = string + "/"
        string = string + ">"
        return string

    def __split_str(string):
        """
        Splits a string at every " and ', but only if those characters are not in a string delimited by the other type of string symbol
        """
        out = []
        while '"' in string or "'" in string: # While there are more attributes in the string
            try:
                if 0 <= string.find('"') < string.find("'") or string.find("'") == -1: # If " comes before ':
                    attr, value, string = string.split('"', 2) # Split off the first attr
                else:
                    attr, value, string = string.split("'", 2)
            except ValueError: # In case a closing character cannot be found:
                raise
                raise EOFError(f"Unclosed attribute value string: '{string}'")
            out.append((attr, value))
        return out

    def __in_str(string, index):
        """
        Tests if a character / index is inside a 'string' (section delimited by quotation marks)

        Returns True if in a string, False otherwise.
        """
        search_index = 0
        while True:
            search_index = min((i for i in [string.find('"', search_index), string.find("'", search_index)] if i >= 0), default = -1) # Search for the opening quotation
            if search_index == -1 or index <= search_index: # If no opening quotation is present at all, or the index was before opening quotation:
                return False
            search_index = string.find(string[search_index], search_index + 1) + 1 # Search for the closing quotation (which has to be the same char as the opening quotation)
            if search_index == 0 or index < search_index: # If either no closing quotation was found, or the index is before the closing quotation:
                return True

    @staticmethod
    def encode(string):
        """
        Encodes a string such that all "forbidden" characters are correctly escaped

        Note: It is not required (nor recommended) to pass the encoded string as the value for an attribute / database entry. Doing this anyway will lead to the strings being double-encoded, since the strings are automatically encoded during saving / writing.
        """
        chars = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;"}
        for char, encoded in chars.items():
            string = string.replace(char, encoded)
        return string

    @staticmethod
    def decode(string):
        """
        Decodes a string such that all escaped characters are replaced with their original characters

        Note: It is not required (nor recommended) to call this function on the database entries / attribute values in the XML structure, as all strings are automatically decoded during parsing.
        """
        #Replace all "alternative" escape sequences with a singular "base" case, which can then be more easily replaced using str.replace, without having to worry about accidentally double-decoding a string / character.
        alts = {"&#38;": "&amp;", "&#60;": "&lt;", "&#62;": "&gt;", "&#34;": "&quot;", "&#39;": "&apos;"}
        for alt, base in alts.items():
            string = string.replace(alt, base)
        #Replace the base escape sequences with their unencoded value
        chars = {"&apos;": "'", "&quot;": '"', "&gt;": ">", "&lt;": "<", "&amp;": "&"}
        for encoded, char in chars.items():
            string = string.replace(encoded, char)
        return string
