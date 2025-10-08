
#nimmt einen purl entgegen und gibt die Einzelteile als Liste aus. Ist ein
#scheme:title/namespace/name@version?qualifiers#subpath
def parse(purl):
    _purlScheme = purl[:4]
    _purlURL = purl[4:]
    _purlComponents = _purlURL.split("/")
    _purlComponents = list(filter(lambda x: len(x) > 0, _purlComponents))

    #Darf ein Purl nur eines jeder Trennzeichen haben?
    if isValidPurl(_purlScheme, _purlComponents):
        return splitComponents(_purlComponents)
    print("Ist keine Purl!!!")

#Überprüft ob die Anforderungen an ein PURL gegeben sind
def isValidPurl(scheme, components):
    #auch noch auf zu viele @, ?, # prüfen?
    return scheme == "pkg:" and len(components) >= 2 and len(components) < 4

#Teilt den Purl in die einzelnen Komponenten
def splitComponents(components):
    _componentList = [components[0]]
    if len(components) == 3:
        _componentList.append(components[1])
    else:
        _componentList.append(None)
    _componentList.extend(splitOptionalComponents(components[-1]))
    return _componentList

#Teilt, wenn vorhanden, die optionalen Komponenten aus dem Purl heraus
def splitOptionalComponents(string):
    _componentList = []
    _string = string
    _separators = ["#", "?", "@"]

    for i in _separators:
        _split = _string.split(i)
        if len(_split) > 1:
            _componentList.append(_split[1])
        else:
            _componentList.append(None)
        _string = _split[0]

    _componentList.append(_string)
    _componentList.reverse()
    return(_componentList)

#Parst eine Liste an purls
def parseList(purlList):
    _parsedList = []
    for i in purlList:
        _parse = parse(i)
        if _parse != None:
            _parsedList.append(parse(i))
    return _parsedList

#Druckt eine geparste Purl in die Konsole
def printPurl(purl):
    _purlComponents = ["Titel", "Namespace", "Name", "Version", "Qualifier", "Subpath"]

    for i in range(6):
        if purl[i] != None:
            print(_purlComponents[i] + ": " + purl[i])
        
def main():
    print("Parse:")
    printPurl(parse("pkg:title//namespace/name@version?qualifier#subpath"))
    print("Parse was anderes:")
    printPurl(parse("pkg:asd/asd@adf#jjjj"))

if __name__ == "__main__":
    main()

