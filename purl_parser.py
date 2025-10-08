
#nimmt einen purl entgegen und gibt die Einzelteile als Liste aus
#scheme:title/namespace/name@version?qualifiers#subpath
def parse(purl):
    _purlSchema = purl[:4]
    _purlURL = purl[4:]
    _purlKomponenten = _purlURL.split("/")

    if istRichtigerPurl(_purlSchema, _purlKomponenten):
        return teileInKomponenten(_purlKomponenten)

#Überprüft ob die Anforderungen an ein PURL gegeben sind
def istRichtigerPurl(schema, komp):
    return schema == "pkg:" and len(komp) >= 2

#Teilt den Purl in die einzelnen Komponenten
def teileInKomponenten(komponenten):
    _listeKomponenten = [komponenten[0]]
    if len(komponenten) == 3:
        _listeKomponenten.append(komponenten[1])
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
        _string = _split[0]
    
    _komponentenliste.append(_string)
    _komponentenliste.reverse()
    return(_komponentenliste)

def parseListe(purlListe):
    _geparstePurls = []
    for i in purlListe:
        _parse = parse(i)
        if _parse != None:
            _geparstePurls.append(parse(i))
    return _geparstePurls

def main():
    print("Parse:")
    parse("pkg:title/namespace/name@version?qualifier#subpath")
    parse("pkg:bitbucket/birkenfeld/pygments-main@244fd47e07d1014f0aed9c")
    print("Parse: falsch")
    parse("pk:itle/namespace/name@version?qualifier#subpath")
    parse("pkg:asdafdssdfjhsdfkj")

if __name__ == "__main__":
    main()