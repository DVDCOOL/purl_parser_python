from constants import *

#Takes a purl as a string and outputs the components as a list 
#scheme:title/namespace/name@version?qualifiers#subpath
class purl_parser:
    def __init__(self, purl):
        self.purl = purl
        
        self.scheme = None
        self.components = []
        self.title = None
        self.namespace = None
        self.name = None
        self.packageComponents = []
        self.version = None
        self.qualifiers = None
        self.subpath = None
        self.separators = [SEPARATOR_FOR_SUBPATH, SEPARATOR_FOR_QUALIFIER, SEPARATOR_FOR_VERSION]
        
        self.parse()
        
    def parse(self):
        if isinstance(self.purl, str) and len(self.purl) > len(PURL_PREFIX):
            self.scheme = self.purl[:len(PURL_PREFIX)]
            self.components = list(filter(lambda x: len(x) > 0, self.purl[len(PURL_PREFIX):].split(SEPARATOR_FOR_NAME)))

            #Darf ein Purl nur eines jeder Trennzeichen haben?
            if self.isValidPurl():
                self.splitComponents()
                self.splitPackageComponents()
            else:
                print("Ist keine Purl!!!")

    #Checks whether the basic requirements for a purl are met
    def isValidPurl(self):
        #auch noch auf zu viele @, ?, # prüfen?
        enoughComponents = len(self.components) >= PURL_MINIMUM_NUMBER_OF_COMPONENTS and len(self.components) <= PURL_MAXIMUM_NUMBER_OF_COMPONENTS

        validSeperatorNumber = True
        for i in self.separators:
            if self.components[PURL_PACKAGE_INDEX].count(i) > 1:
                validSeperatorNumber = False

        return self.scheme == PURL_PREFIX and enoughComponents and validSeperatorNumber

    #Splits the purl into its components
    def splitComponents(self):
        self.title = self.components[PURL_TITLE_INDEX]
        if len(self.components) == PURL_MAXIMUM_NUMBER_OF_COMPONENTS:
            self.namespace = self.components[PURL_NAMESPACE_INDEX]
        else:
            self.namespace = None


    #splits the purl into its optional components
    def splitPackageComponents(self):
        packageToSplit = self.components[PURL_PACKAGE_INDEX]
        
        for i in self.separators:
            #split from the right side, so that the name is always at the front
            component = packageToSplit.split(i)
            if len(component) > 1:
                self.packageComponents.append(component[1])
            else:
                self.packageComponents.append(None)
            packageToSplit = component[0]
            
        self.packageComponents.append(packageToSplit)
        self.packageComponents.reverse()

        self.name = self.packageComponents[PACKAGE_NAME_INDEX]
        self.version = self.packageComponents[PACKAGE_VERSION_INDEX]
        self.qualifiers = self.packageComponents[PACKAGE_QUALIFIER_INDEX]
        self.subpath = self.packageComponents[PACKAGE_SUBPATH_INDEX]




