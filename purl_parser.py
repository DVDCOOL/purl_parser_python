
#nimmt einen purl entgegen und gibt die Einzelteile als Liste aus
#scheme:title/namespace/name@version?qualifiers#subpath
def parse(purl):
    _purl = purl
    _purlSchema = _purl[:4]
    _purlURL = _purl[4:]
    _purlKomponenten = _purlURL.split("/")

    if not istRichtigerPurl(_purlSchema, _purlKomponenten):
        print("Invalider PURL")
    else:
        geparsterPurl = teileInKomponenten(_purlKomponenten)
        print(*geparsterPurl, sep= ", ")
        return geparsterPurl
 
#Überprüft ob die Anforderungen an ein PURL gegeben sind
def istRichtigerPurl(schema, komp):
    _schema = schema
    _komp = komp
    return _schema == "pkg:" and len(_komp) >= 2

#Teilt den Purl in die einzelnen Komponenten
def teileInKomponenten(komponenten):
    _komponenten = komponenten
    _listeKomponenten = []
    _listeKomponenten.append(komponenten[0])
    if len(_komponenten) == 3:
        _listeKomponenten.append(_komponenten[1])
    _listeKomponenten.extend(teileInOptionaleKomponenten(_komponenten[-1]))
    return _listeKomponenten

#Teilt, wenn vorhanden, die optionalen Komponenten aus dem Purl heraus
def teileInOptionaleKomponenten(string):
    _komponentenliste = []
    _string = string
    if "#" in string:
        _komponentenliste.append(_string.split("#")[1])
        _string = _string.split("#")[0]
    if "?" in string:
        _komponentenliste.append(_string.split("?")[1])
        _string = _string.split("?")[0]
    if "@" in string:
        _komponentenliste.append(_string.split("@")[1])
        _string = _string.split("@")[0]
    _komponentenliste.append(_string)
    _komponentenliste.reverse()
    return(_komponentenliste)

def main():
    print("Parse:")
    parse("pkg:title/namespace/name@version?qualifier#subpath")
    parse("pkg:bitbucket/birkenfeld/pygments-main@244fd47e07d1014f0aed9c")
    print("Parse: falsch")
    parse("pk:itle/namespace/name@version?qualifier#subpath")
    parse("pkg:asdafdssdfjhsdfkj")

if __name__ == "__main__":
    main()

