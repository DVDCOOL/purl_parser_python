from constants import *

#Takes a purl as a string and outputs the components as a list 
#scheme:title/namespace/name@version?qualifiers#subpath
class PurlParser:
    def __init__(self, purl):
        self.inputPurl = purl
        self.purl = self.inputPurl
        
        self.validPurl = True
        self.scheme = None
        self.type = None
        self.namespace = None
        self.name = None
        self.version = None
        self.qualifiers = None
        self.listOfQualifiers = []
        self.subpath = None

        self.parse()
        
    def parse(self):
        if isinstance(self.purl, str) and len(self.purl) > len(PURL_PREFIX)+1 and len(self.purl) <= MAX_PURL_LENGTH:
            self.purl = self.purl.replace(" ", "")
            self.parseSubpath()
            self.parseQualifier()
            self.parseScheme()
            self.parseType()
            self.parseVersion()
            self.parseName()
            self.parseNamespace()
        else:
            self.validPurl = False

            
    def parseSubpath(self):
        purlSplit = self.purl.split(SEPARATOR_FOR_SUBPATH)
        if len(purlSplit) > 1:
            subpath_string = purlSplit[-1]
            segments = [s for s in subpath_string.split('/') 
                    if s and s not in ('.', '..')]
            self.subpath = '/'.join(segments) if segments else None
            self.updatePurlIfComponentAtTheback(subpath_string)


    def parseQualifier(self):
        purlSplit = self.purl.split(SEPARATOR_FOR_QUALIFIER)
        if len(purlSplit) > 1:
            self.qualifiers = purlSplit[-1]
            key_and_values = self.qualifiers.split(SEPARATOR_BETWEEN_QUALIFIERS)
            for i in key_and_values:
                if len(i.split(SEPARATOR_BETWEEN_KEY_AND_VALUE)) == 2:
                    self.listOfQualifiers.append(i.split(SEPARATOR_BETWEEN_KEY_AND_VALUE))
                else:
                    self.validPurl = False
            self.updatePurlIfComponentAtTheback(self.qualifiers)
    
    def parseScheme(self):
        if len(self.purl.split(SEPARATOR_FOR_SCHEME)) > 1:
            self.scheme = self.purl.split(SEPARATOR_FOR_SCHEME)[0].lower()
            self.purl = self.purl[len(self.scheme)+1:]
            self.purl = self.purl.lstrip('/')  # Add this line
            if self.scheme != PURL_PREFIX:
                self.validPurl = False
        else:
            self.validPurl = False

    def parseType(self):
        purlSplit = self.splitComponentsByNameSeparator()
        if len(purlSplit) > 1:
            self.type = purlSplit[0].lower()
            self.purl = self.purl[len(self.type)+1:]  
        else:
            self.validPurl = False
    
    def parseVersion(self):
        purlSplit = self.purl.split(SEPARATOR_FOR_VERSION)
        if len(purlSplit) > 1:
            self.version = purlSplit[-1]
            self.updatePurlIfComponentAtTheback(self.version)
        self.purl = self.purl.rstrip('/')  # Add this line (outside the if)
    
    def parseName(self):
        purlSplit = self.splitComponentsByNameSeparator()
        if self.purl != "":
            if len(purlSplit) > 1:
                self.name = purlSplit[-1]
                self.updatePurlIfComponentAtTheback(self.name)
            elif purlSplit[0] != "":
                self.name = self.purl
                self.purl = ""
            else:
                self.validPurl = False
        else:
            self.validPurl = False 
    
    def parseNamespace(self):
        purlSplit = self.purl.rstrip('/').lstrip('/')

        if purlSplit:
            self.namespace = purlSplit
    
    def splitComponentsByNameSeparator(self):
        return list(filter(lambda x: len(x) > 0, self.purl.split(SEPARATOR_FOR_NAME)))
    
    def updatePurlIfComponentAtTheback(self, component_to_remove):
        self.purl = self.purl[:len(self.purl) - len(component_to_remove) -1]
        


   