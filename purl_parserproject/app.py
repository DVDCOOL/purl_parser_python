from purl_parser import PurlParser
from purls import purls

#for showcase example purposes           
def main():
    purlsIsCorrect = True
    index = 0
    while purlsIsCorrect and index < len(purls):
        purl = purls[index]
        parsedPurl = PurlParser(purl)
        purlsIsCorrect =  parsedPurl.validPurl
        index += 1
    if purlsIsCorrect:
        print(f"All {len(purls)} purls are correctly formed.")
    else:
        print(f"The purl at index {index-1} is not correctly formed: {purls[index-1]}")


if __name__ == "__main__":
    main()
