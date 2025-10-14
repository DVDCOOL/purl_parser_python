
# purl_parser Documentation

Splits up purls into their components. The structure of a purl is the following

scheme:title/namespace/name@version?qualifiers#subpath

A parsed purl will have a separated title, namespace, name, version, qualifier and subpath. This parser does not percent-decode the components yet.

## parse(purl)
purl        -> str

returns     -> list[str]

Method takes a String as a Parameter, checks if it has all the mandatory components of a purl using isValidPurl() and returns the parsed String components in a List without separator characters and without the scheme. If an optional component is not present, the list will contain None in its place. If the Parameter is not a String or not a Purl, this Method will return None and print a warning on the console.

## isValidPurl(scheme, components)
scheme      -> str
components  -> list[str]

returns     -> boolean

Checks whether the Parameters belong to a purl or not. Will return True if the Scheme of the purl is "pkg:" and the right number of components and no more than one of every seperator character is present.

## splitComponents(components)
components  -> list[str]

returns     -> list[str]

Splits the main components of a purl (minus the scheme) and the optional namespace.

## splitOptionalComponents(string)
string      -> str

returns      -> list[str]

Splits the optional components of a purl at the separator characters, starting from right to left and returns them in a list. If no separator characters are present in the string, the string will be returned in a list as-is.

## parseList(purlList)
purlList    -> list[str]

returns     -> list[list[str]]

Parses a list of strings and returns all components in a nested list.

## printPurl(purl)
purl        -> list[str]

Takes a parsed purl as a parameter and prints the components with their descriptor on the console.