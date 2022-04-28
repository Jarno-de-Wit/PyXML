"""
XML Parser / Editor / Creator
"""
import itertools as it

class XML():
    def __init__(self, name = "", tag_type = "auto"):
        self.name = name
        self.attributes = {}
        self.database = []
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
        for line in data:
            if data[0][0:1] == "<":
                if data[0][1:2] == "?":
                    data.pop(0)
                elif data[0][1:2] == "!":
                    data.pop(0)
                else:
                    return cls.XML_from_str("".join(line.rstrip("\n").lstrip(" \t") for line in data))
            else:
                data.pop()
        raise RuntimeError("Couldn't read XML File. Does the file contain a valid XML structure?")

    @classmethod
    def XML_from_str(cls, data, return_trailing = False):
        """
        Loads an XML structure from a string

        data: string - string to be parsed to an XML structure. Should not contain any newline characters.
        return_trailing: bool - determines whether the text after the parsed element should be returned.
        """
        self = cls() #Set up an XML object to return in the end

        #Find the header position ----------------------------------------------
        header_end = 0
        while True:
            header_end = data.index(">", header_end + 1) #Search for the ">" header ender, starting from the spot after the previous position.
            if not data[:header_end].count('"') % 2: #If the ">" was not encased by double quotation marks, and thus was not part of a string / value:
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
        self.name = header_data[0] #Extract the tag name, by removing the leading "<"
        if len(header_data) == 2: #If the tag contained any attributes:
            attributes = header_data[1].split('"') #Split the header data at each ", to separate the attributes from their value
            attr_names = attributes[0::2] #The names are given by all items index i=0+2n
            attr_data  = attributes[1::2] #The data  is  given by all items index i=1+2n
            for attr in zip(attr_names, attr_data):
                self.attributes[attr[0].replace("=", "").strip(" ")] = attr[1] #Set the attribute in the attributes list. For the attribute name, any leading/trailing spaces, and the "=" sign are removed. The data is left unchanged, as anything withing the '"' was part of the string anyway.
        if self.type == "short": #If the tag is of the short type, and thus consists only of a "header", return it now.
            if return_trailing: #If requested, also return all unused "trailing" data
                return self, data[header_end:]
            else:
                return self

        #Decode the body of the XML tag ----------------------------------------
        data = data[header_end:]
        data = data.lstrip(" \t")
        while index := data.find(f"</{self.name}>"): #While the next part in the data is not this data's own end tag, there must be another child in between:
            if index == -1:
                raise EOFError(f"No valid closing tag found for tag with name '{self.name}'")
            if tag_index := data.find("<"): #If the next part is text, and not an XML tag:
                child = data[:tag_index]
                data = data[tag_index:]
            else:
                child, data = cls.XML_from_str(data, return_trailing = True)
            self.database.append(child) #Append the tag to the database
            data = data.lstrip(" \t") #Strip any " " that are between two XML tags, that now suddenly are on the outside of the data.

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
        self.database.append(value)


    def keys(self):
        keys = list(self.attributes.keys())
        return keys

    def __str__(self):
        return f"<XML object {self.name}>"

    def __repr__(self):
        return f"<XML object {self.name} with keys {self.keys()} and {len(self.database)} children>"

    def test_attr(self, attributes, values = None):
        """
        Tests if an XML object has the requested attributes, and if these attributes are set to the given values

        attributes: str / iterable - A (list of) attribute names that should be checked
        values: NoneType / str / iterable - The respective values the attributes should have. Set to None to accept any value as correct.

        returns: Bool - True if criteria are met, False otherwise
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

    def get_filtered(self, attribute, value = None, recursion_depth = 1, sort = True):
        """
        Returns the first item in the database, for which the value of "attribute" is equal to "value".
        If value is None, returns the first item that has the given attribute.
        Useful for example when there is a list of parts, each having an attribute "id", where you want to find a part with a specific id.
        """
        return next((tag for tag in self.iter_tags(recursion_depth, sort) if tag.test_attr(attribute, value)), None)

    def get_filtered_all(self, attribute, value = None, recursion_depth = 1, sort = True):
        """
        Returns all items in the database, for which the value of "attribute" is equal to "value".
        If value is None, returns all items that have the given attribute.
        Recursion depth determines up to how many levels deep the search should go. Set to < 0 for unlimited recursion.
        """
        return [tag for tag in self.iter_tags(recursion_depth, sort) if tag.test_attr(attribute, value)]

    def find(self, name, recursion_depth = 1, sort = True):
        """
        Returns the first tag which has the given tag.name
        """
        return next((tag for tag in self.iter_tags(recursion_depth, sort) if tag.name == name), None)

    def find_all(self, name, recursion_depth = 1, sort = True):
        """
        Returns all tags which have the given tag.name
        """
        return [tag for tag in self.iter_tags(recursion_depth, sort) if tag.name == name]

    def iter_database(self, recursion_depth = -1, sort = True, nested_tree = False):
        """
        Returns a tuple of all nested items, nested up to a depth of 'recursion_depth'.
        If recursion_depth is < 0; recursion is unlimited.
        If sort is True, all items are returned sorted based on their nesting level. Else, all items are returned in a tree order.
        If nested_tree is True, will not return a flat tuple, but will instead return a (one level) nested tuple of all items, based on their nesting level. Requires sort to be True.
        """
        if sort and nested_tree:
            return ((self,),) + (tuple(sum(i, ()) for i in it.zip_longest(*(child.iter_database(recursion_depth - 1, True, True)if isinstance(child, XML) else ((child,),)  for child in self.database), fillvalue = ())) if recursion_depth else ())
        elif sort:
            #Simply flatten the nested_tree sorted list
            return sum(self.iter_database(recursion_depth, True, True), ())
        else:
            return sum((child.iter_database(recursion_depth - 1, False) if isinstance(child, XML) else (child,) for child in self.database), (self,)) if recursion_depth else (self,)

    def iter_tags(self, recursion_depth = -1, sort = True, nested_tree = False):
        """
        Returns a tuple of all nested tags, nested up to a depth of 'recursion_depth'.
        If recursion_depth is < 0; recursion is unlimited.
        If sort is True, all items are returned sorted based on their nesting level. Else, all items are returned in a tree order.
        If nested_tree is True, will not return a flat tuple, but will instead return a (one level) nested tuple of all items, based on their nesting level. Requires sort to be True.
        """
        if sort == True and nested_tree == True:
            return tuple(tuple(tag for tag in branch if isinstance(tag, XML)) for branch in self.iter_database(recursion_depth, sort, nested_tree))
        else:
            return tuple(tag for tag in self.iter_database(recursion_depth, sort, nested_tree) if isinstance(tag, XML))

    @property
    def max_depth(self):
        """
        Returns the maximum depth of any of its children
        """
        if not self.database:
            return 0
        else:
            return 1 + max(child.max_depth for child in self.database)

    def write(self, file, depth = 0):
        """
        Write the XML structure to a given file

        file: string / filepath - The path to the file the XML should be stored to.
        depth: int - The indentation (in '  ') the XML tag should have by default.
        """
        if not hasattr(file, "write"):
            with open(file, "w", encoding = "utf-8-sig") as file:
                file.write('<?xml version="1.0" encoding="utf-8"?>\n') #Write the header
                file.write(f"{depth * '  '}{self.header}\n")
                for child in self.database:
                    child.write(file, depth + 1)
                if self.type == "long" or (self.type == "auto" and self.database):
                    file.write(f"{depth * '  '}</{self.name}>") #No \n at the end, as this is the first, and thus also the last item.
        else:
            file.write(f"{depth * '  '}{self.header}\n")
            for child in self.database:
                child.write(file, depth + 1)
            if self.type == "long" or (self.type == "auto" and self.database):
                file.write(f"{depth * '  '}</{self.name}>\n")


    @property
    def header(self):
        """
        Builds the header string for writing the XML tag to a file
        """
        string = f"<{self.name}"
        for attr in self.attributes:
            value = str(self.attributes[attr]).removeprefix('"').removesuffix('"') #Turn the value into a string, without any " surrounding it.
            string = " ".join([string, f'{attr}="{value}"'])
        if self.type == "short" or (self.type == "auto" and not self.database): #If the tag is of the short type, add the "/" to the end to signify this.
            string = string + "/"
        string = string + ">"
        return string
