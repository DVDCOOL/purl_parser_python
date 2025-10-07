purl_to_check = input("Input PURL to parse: ")
type = "" #Type of PURL - Mandetory
namespace = "" #Namespace - Optional
name = "" #Name of package - Mandetory
version = "" #Version of package - Optional
qualifires = "" #Qualifires for the package - Optional
subpath = "" #Subpath of package - Optional

# pkg:type/namespace/name@version?qualifires#subpath

pkg_string = purl_to_check[:4]

if pkg_string == "pkg:" :
    purl_spec = purl_to_check[4:].split("/")
    #type  /  namespace  /   name@version?qualifires#subpath
    if len(purl_spec) < 2:
        print("Not a correct PURL")
    else:
        if len(purl_spec) == 3:
            namespace = purl_spec[1]          
        type = purl_spec[0]
        package = purl_spec[-1].split("@")
        if len(package) == 0:
            print("Not a correct PURL") 
        else:
            name = package[0]
            package_spec = package[1].split("?")
            version = package_spec[0]
            if len(package_spec) > 1:
                package_q_and_s = package_spec[1].split("#")
                qualifires = package_q_and_s
                if len(package_spec) > 1:
                    subpath = package_q_and_s
            print("Type: " + type)
            print("Namespace: "+namespace)
            print("Name: "+name)
            print("Version: "+version)
            print("Qualifires: "+qualifires)
            print("Subpath: "+subpath)

else:
    print("Not a correct PURL")