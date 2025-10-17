from purl_parser import PurlParser

#for showcase example purposes           
def main():
    print("Parse:")
    purl1 = PurlParser("pkg:title///namespace///name@version?qualifier#subpath")
    print(purl1.type)
    print(purl1.namespace)
    print(purl1.name)
    print(purl1.version)
    print(purl1.qualifiers)
    print(purl1.subpath)
    print(purl1.validPurl)
    print("")
    print("Parse was anderes:")
    purl2 = PurlParser("pkg:asd/asd@adf#jjjj")
    print(purl2.type)
    print(purl2.namespace)
    print(purl2.name)
    print(purl2.version)
    print(purl2.qualifiers)
    print(purl2.subpath)
    print(purl1.validPurl)


if __name__ == "__main__":
    main()
