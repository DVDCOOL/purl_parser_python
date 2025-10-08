
#nimmt einen purl entgegen und gibt die Einzelteile als Liste aus
#scheme:title/namespace/name@version?qualifiers#subpath
def parse(purl):
    _purlSchema = purl[:4]
    _purlURL = purl[4:]
    _purlKomponenten = _purlURL.split("/")
    _purlKomponenten = list(filter(lambda x: len(x) > 0, _purlKomponenten))

    #Darf ein Purl nur eines jeder Trennzeichen haben?
    if istRichtigerPurl(_purlSchema, _purlKomponenten):
        return teileInKomponenten(_purlKomponenten)
    print("Ist keine Purl!!!")

#Überprüft ob die Anforderungen an ein PURL gegeben sind
def istRichtigerPurl(schema, komp):
    return schema == "pkg:" and len(komp) >= 2 and len(komp) < 4

#Teilt den Purl in die einzelnen Komponenten
def teileInKomponenten(komponenten):
    _listeKomponenten = [komponenten[0]]
    if len(komponenten) == 3:
        _listeKomponenten.append(komponenten[1])
    else:
        _listeKomponenten.append(None)
    _listeKomponenten.extend(teileInOptionaleKomponenten(komponenten[-1]))
    return _listeKomponenten

#Teilt, wenn vorhanden, die optionalen Komponenten aus dem Purl heraus
def teileInOptionaleKomponenten(string):
    _komponentenliste = []
    _string = string
    _separators = ["#", "?", "@"]

    for i in _separators:
        _split = _string.split(i)
        if len(_split) > 1:
            _komponentenliste.append(_split[1])
        else:
            _komponentenliste.append(None)
        _string = _split[0]
    
    _komponentenliste.append(_string)
    _komponentenliste.reverse()
    return(_komponentenliste)

#Parst eine Liste an purls
def parseListe(purlListe):
    _geparstePurls = []
    for i in purlListe:
        _parse = parse(i)
        if _parse != None:
            _geparstePurls.append(parse(i))
    return _geparstePurls

#Druckt eine geparste Purl in die Konsole
def printPurl(purl):
    _komponentenPurl = ["Titel", "Namespace", "Name", "Version", "Qualifier", "Subpath"]

    for i in range(6):
        if purl[i] != None:
            print(_komponentenPurl[i] + ": " + purl[i])
        
def main():
    print("Parse:")
    printPurl(parse("pkg:title//namespace/name@version?qualifier#subpath"))
    print("Parse was anderes:")
    printPurl(parse("pkg:asd/asd@adf#jjjj"))

if __name__ == "__main__":
    main()

