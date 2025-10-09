
#Takes a purl as a string and outputs the components as a list 
#scheme:title/namespace/name@version?qualifiers#subpath
def parse(purl):
    if isinstance(purl, str):
        _purlScheme = purl[:4]
        _purlURL = purl[4:]
        _purlComponents = _purlURL.split("/")
        _purlComponents = list(filter(lambda x: len(x) > 0, _purlComponents))

        #Darf ein Purl nur eines jeder Trennzeichen haben?
        if isValidPurl(_purlScheme, _purlComponents):
            return splitComponents(_purlComponents)
    print("Ist keine Purl!!!")

#Checks whether the basic requirements for a purl are met
def isValidPurl(scheme, components):
    #auch noch auf zu viele @, ?, # prüfen?
    enoughComponents = len(components) >= 2 and len(components) < 4
    validSeperatorNumber = True
    _separators = ["#", "?", "@"]
    for i in _separators:
        if components[-1].count(i) > 1:
            _separators = False
    return scheme == "pkg:" and len(components) >= 2 and len(components) < 4

#Splits the purl into its components
def splitComponents(components):
    _componentList = [components[0]]
    if len(components) == 3:
        _componentList.append(components[1])
    else:
        _componentList.append(None)
    _componentList.extend(splitOptionalComponents(components[-1]))
    return _componentList

#splits the purl into its optional components
def splitOptionalComponents(string):
    _componentList = []
    _stringToSplit = string
    _separators = ["#", "?", "@"]

    for i in _separators:
        _split = _stringToSplit.split(i)
        if len(_split) > 1:
            _componentList.append(_split[1])
        else:
            _componentList.append(None)
        _stringToSplit = _split[0]

    _componentList.append(_stringToSplit)
    _componentList.reverse()
    return(_componentList)

#Parsed a list of purls
def parseList(purlList):
    _parsedList = []
    for i in purlList:
        _parse = parse(i)
        if _parse != None:
            _parsedList.append(parse(i))
    return _parsedList

#Prints a parsed purl into the console
def printPurl(purl):
    _purlComponents = ["Titel", "Namespace", "Name", "Version", "Qualifier", "Subpath"]

    for i in range(6):
        if purl[i] != None:
            print(_purlComponents[i] + ": " + purl[i])

#for showcase example purposes           
def main():
    print("Parse:")
    printPurl(parse("pkg:title//namespace/name@version?qualifier#subpath"))
    print("Parse was anderes:")
    printPurl(parse("pkg:asd/asd@adf#jjjj"))

if __name__ == "__main__":
    main()

