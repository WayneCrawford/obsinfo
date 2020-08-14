import xml.etree.ElementTree as ET

error = lambda s: "\033[91m" + s + "\033[0m"


class XmlTree:

    ns = "{http://www.fdsn.org/xml/station/1}"

    @staticmethod
    def convert_string_to_tree(xmlString):

        return ET.fromstring(xmlString)

    @staticmethod
    def getroot(xml):
        return xml.getroot()

    @staticmethod
    def add_ns(tag):
        return f"{XmlTree.ns}{tag}"

    def xml_compare(self, x1, x2, excludes=["Created"],
                    excludes_attributes=[]):
        """
        Compares two xml etrees
        :param x1: the first tree
        :param x2: the second tree
        :param excludes: list of string of attributes to exclude from
            comparison
        :return:
            True if both files match
        """
        # get namespace

        if x1.tag != x2.tag:
            return False, error(f"Tags do not match: {x1.tag} and {x2.tag}")
        for name, value in x1.attrib.items():
            if name not in excludes_attributes:
                if x2.attrib.get(name) != value:
                    print(error("Attributes do not match: {}={}, {}={}"
                        .format(name, value, name, x2.attrib.get(name))))
                    print(error(f"Elements: {x1.attrib},{x2.attrib}"))
                    return False
        for name in x2.attrib.keys():
            if name not in excludes:
                if name not in x1.attrib:
                    print("x2 has an attribute x1 is missing: %s" % name)

                    return False
        if not self.text_compare(x1.text, x2.text):
            print(error(f"text: {x1.text} != {x2.text}"))
            print(error(f"Elements: {x1.tag},{x2.tag}"))
            return False
        if not self.text_compare(x1.tail, x2.tail):
            print("tail: %r != %r" % (x1.tail, x2.tail))
            return False
        cl1 = list(x1)
        cl2 = list(x2)

        if len(cl1) != len(cl2):
            print(error(f"children length differs, {len(cl1)}!= {len(cl2)}"))
            return False
        i = 0
        for c1, c2 in zip(cl1, cl2):
            i += 1
            if c1.tag not in excludes:
                if not self.xml_compare(c1, c2, excludes, excludes_attributes):
                    print(c1.attrib, c2.attrib)
                    print(error(
                        f"children {c1.tag} do not match with {c1.tag}"))
                    return False
        return True

    def text_compare(self, t1, t2):
        """
        Compare two text strings
        :param t1: text one
        :param t2: text two
        :return:
            True if a match
        """
        if not t1 and not t2:
            return True
        if t1 == "*" or t2 == "*":
            return True
        return (t1 or "").strip() == (t2 or "").strip()


def main():
    print("Should not be run alone")


if __name__ == "__main__":
    main()
