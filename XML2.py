"""
XML Parser / Editor / Creator
"""
class XML():
    def __init__(self, name = "", tag_type = "auto"):
        self.name = name
        self.attributes = {}
        self.database = []
        self.type = tag_type

    @classmethod
    def XMLFile(cls, filepath = None):
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
                    return cls.XML_from_str("".join(line.rstrip("\n") for line in data))
            else:
                data.pop()
        print(data)
        raise RuntimeError("Couldn't read XML File")

    @classmethod
    def XML_from_str(cls, data, return_data = False):
        self = cls() #Set up an XML object to return in the end

        #Find the header position ----------------------------------------------
        header_end = 0
        while True:
            header_end = data.index(">", header_end + 1) #Search for the ">" header ender, starting from the spot after the previous position.
            if not data[:header_end].count('"') % 2: #If the ">" was not encased by ", and thus was not part of a string:
                header_end += 1 #Move the index over by 1, so it ends using [:header_end] as an index also includes the ">" itself
                break #Break out of the while loop. The ">" has been found.

        #Decode the header -----------------------------------------------------
        header_data = data[:header_end].removeprefix("<").removesuffix(">")

        if header_data[-1] == "/" or header_data[-1] == "?":
            self.type = "short"
            header_data = header_data.removesuffix("/").removesuffix("?") #Remove the trailing "/" if it exists (which would indicate a short tag)
        else:
            self.type == "long"
        header_data = header_data.split(" ", 1) #Split the header into: [0] The tag name; [1] The attribute list
        self.name = header_data[0] #Extract the tag name, by removing the leading "<"
        if len(header_data) == 2: #If the tag contained any attributes:
            attributes = header_data[1].split('"') #Split the header data at each ", to separate the attributes from their data.
            attr_names = attributes[0::2] #The names are given by all items index i=0+2n
            attr_data  = attributes[1::2] #The data  is  given by all items index i=1+2n
            for attr in zip(attr_names, attr_data):
                self.attributes[attr[0].replace("=", "").strip(" ")] = attr[1] #Set the attribute in the attributes list. For the attribute name, any leading/trailing spaces, and the "=" sign are removed. The data is left unchanged, as anything withing the '"' was part of the string anyway.
        if self.type == "short": #If the tag is of the short type, and thus consists only of a "header", return it now.
            if return_data: #If requested, also return all unused "trailing" data
                return self, data[header_end:]
            else:
                return self

        #Decode the body of the XML tag ----------------------------------------
        global b
        b = self
        data = data[header_end:]
        data = data.strip(" ")
        if data[0] != "<":
            return (self.name, data[:data.index(f"</{self.name}>")]), data[data.index(f"</{self.name}>") + len(f"</{self.name}>"):]
        while data.index(f"</{self.name}>"): #While the next part in the data is not this data's own end tag, there must be another child in between:
            child, data = cls.XML_from_str(data, return_data = True)
            if isinstance(child, XML):
                self.database.append(child) #Append the tag to the database
            else:
                self.attributes[child[0]] = child[1]
            data = data.strip(" ") #Strip any " " that are between two XML tags, that now suddenly are on the outside of the data.

        #Remove the end tag from the data --------------------------------------
        data = data.removeprefix(f"</{self.name}>")

        #Return whatever data is necessary
        if return_data:
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

    def get_filtered(self, attribute, value = None):
        """
        Returns the first item in the database, for which the value of "attribute" is equal to "value".
        If value is None, returns the first item that has the given attribute.
        Useful for example when there is a list of parts, each having an attribute "id", where you want to find a part with a specific id.
        """
        for item in self.database:
            if attribute in item.keys():
                if value is None or item[attribute] == value:
                    return item
        return None #Return None if item not found

    def get_filtered_all(self, attribute, value = None):
        """
        Returns all items in the database, for which the value of "attribute" is equal to "value".
        If value is None, returns all items that have the given attribute.
        """
        out = []
        for item in self.database:
            if attribute in item.keys():
                if value is None or item[attribute] == value:
                    out.append(item)
        return out

    def write(self, file, xflr = False, depth = 0):
        if not hasattr(file, "write"):
            with open(file, "w", encoding = "utf-8-sig") as file:
                file.write('<?xml version="1.0" encoding="utf-8"?>\n') #Write the header
                if xflr:
                    file.write("<!DOCTYPE explane>\n")
                file.write(f"{depth * '  '}{self.header}\n")
                for child in self.database:
                    child.write(file, xflr, depth + 1)
                if self.type == "long" or (self.type == "auto" and self.database):
                    file.write(f"{depth * '  '}</{self.name}>") #No \n at the end, as this is the first, and thus also the last item.
        else:
            if xflr:
                file.write(f"{depth * '  '}<{self.name}>\n")
                for attribute in self.attributes.items():
                    file.write(f"{(depth + 1) * '  '}<{attribute[0]}>{attribute[1]}</{attribute[0]}>\n")
            else:
                file.write(f"{depth * '  '}{self.header}\n")
            for child in self.database:
                child.write(file, xflr, depth + 1)
            if self.type == "long" or (self.type == "auto" and self.database) or (xflr and self.attributes):
                file.write(f"{depth * '  '}</{self.name}>\n")


    @property
    def header(self):
        string = f"<{self.name}"
        for attr in self.attributes:
            value = str(self.attributes[attr]).removeprefix('"').removesuffix('"') #Turn the value into a string, without any " surrounding it.
            string = " ".join([string, f'{attr}="{value}"'])
        if self.type == "short" or (self.type == "auto" and not self.database): #If the tag is of the short type, add the "/" to the end to signify this.
            string = string + "/"
        string = string + ">"
        return string
