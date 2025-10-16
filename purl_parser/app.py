from purl_parser import purl_parser

#for showcase example purposes           
def main():
    print("Parse:")
    purl1 = purl_parser("pkg:title//namespace/name@version?qualifier#subpath")
    print(purl1.title)
    print(purl1.namespace)
    print(purl1.name)
    print(purl1.version)
    print(purl1.qualifiers)
    print(purl1.subpath)
    print("Parse was anderes:")
    purl2 = purl_parser("pkg:asd/asd@adf#jjjj")
    print(purl2.title)
    print(purl2.namespace)
    print(purl2.name)
    print(purl2.version)
    print(purl2.qualifiers)
    print(purl2.subpath)


if __name__ == "__main__":
    main()
