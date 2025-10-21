from constants import *

#Takes a purl as a string and outputs the components as a list 
#scheme:title/namespace/name@version?qualifiers#subpath
class purl_parser:
    def __init__(self, purl):
        self.purl = purl
        
        self.validPurl = True
        self.scheme = None
        self.componentsToSplit = None
        self.components = []
        self.title = None
        self.namespace = None
        self.name = None
        self.packageToSplit = None
        self.packageComponents = []
        self.version = None
        self.qualifiers = None
        self.listOfQualifiers = []
        self.subpath = None
        self.separators = [SEPARATOR_FOR_SUBPATH, SEPARATOR_FOR_QUALIFIER, SEPARATOR_FOR_VERSION]
        
        self.parse()
        
    def parse(self):
        if isinstance(self.purl, str) and len(self.purl) > len(PURL_PREFIX)+1 and len(self.purl) <= MAX_PURL_LENGTH:
            if len(self.purl.split(SEPERATOR_FOR_SCHEME))>1:
                self.scheme = self.purl.split(SEPERATOR_FOR_SCHEME)[0]
                self.componentsToSplit = self.purl[len(self.scheme)+1:]  
                if self.scheme != PURL_PREFIX:
                    self.validPurl = False
            else:
                self.componentsToSplit = self.purl
                self.validPurl = False
            self.components = list(filter(lambda x: len(x) > 0, self.componentsToSplit.split(SEPARATOR_FOR_NAME)))
            #Darf ein Purl nur eines jeder Trennzeichen haben?
            #auch noch auf zu viele @, ?, # prüfen?
            for i in self.separators:
                if self.components[PURL_PACKAGE_INDEX].count(i) > 1:
                    self.validPurl = False
            enoughComponents = len(self.components) >= PURL_MINIMUM_NUMBER_OF_COMPONENTS
            if enoughComponents:
                self.splitComponents()
            elif len(self.components) == 1:
                self.validPurl = False
                self.packageToSplit = self.components[PURL_PACKAGE_INDEX]
            self.splitPackageComponents()
            if self.qualifiers:
                self.parseQualifier()    
        
            

    #Splits the purl into its components
    def splitComponents(self):
        self.title = self.components[PURL_TITLE_INDEX]
        if len(self.components) == PURL_MAXIMUM_NUMBER_OF_COMPONENTS:
            self.namespace = self.components[PURL_NAMESPACE_INDEX]
            self.packageToSplit = self.components[PURL_PACKAGE_INDEX]
        elif len(self.components) == PURL_MINIMUM_NUMBER_OF_COMPONENTS:
            self.namespace = None
            self.packageToSplit = self.components[PURL_PACKAGE_INDEX]
        else:
            self.validPurl = False
            self.packageToSplit = self.componentsToSplit[len(self.title):]
            slashnum = 0
            for i in self.packageToSplit:
                if i != "/":
                    break
                else:
                    slashnum += 1
            self.packageToSplit = self.componentsToSplit[(len(self.namespace) + slashnum ):]
            slashnum = 0
            for i in self.packageToSplit:
                if i != "/":
                    break
                else:
                    slashnum += 1
            self.packageToSplit = self.componentsToSplit[slashnum:]
            


    #splits the purl into its optional components
    def splitPackageComponents(self):
        
        for i in self.separators:
            #split from the right side, so that the name is always at the front
            component = self.packageToSplit.split(i)
            if len(component) > 1:
                self.packageComponents.append(component[1])
            else:
                self.packageComponents.append(None)
            self.packageToSplit = component[0]
            
        self.packageComponents.append(self.packageToSplit)
        self.packageComponents.reverse()

        self.name = self.packageComponents[PACKAGE_NAME_INDEX]
        self.version = self.packageComponents[PACKAGE_VERSION_INDEX]
        self.qualifiers = self.packageComponents[PACKAGE_QUALIFIER_INDEX]
        self.subpath = self.packageComponents[PACKAGE_SUBPATH_INDEX]
        
    def parseQualifier(self):
        key_and_values = self.qualifiers.split("&")
        for i in self.key_and_values:
            self.listOfQualifiers.append(key_and_values.split("="))
        




