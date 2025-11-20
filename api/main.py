from flask import Flask, jsonify, request
from database.functionsForDB import Database
import os

DB_PATH = os.getenv('DB_PATH', './shared/database/packages.db')

app = Flask(__name__)

@app.route('/get_packages')
def get_packages():
    db = Database(DB_PATH)
    packages = db.getAllPackages()
    output = []
    
    for package in packages:
        purl = package[1]
        type = package[2]
        namespace = package[3]
        name = package[4]
        version = []
        for i in packages[5]:
            version.append({
                'version': i
            })
            
        qualifiers = package[6]
        for i in qualifiers:
            qualifiers.append({
                'key': i[0],
                'value': i[1]
            })
        subpath = package[7]
        for i in subpath:
            subpath.append({
                'subpath': i
            })
        license = []
        
        for i in package[8]:
            license.append({
                'license': i
            })
        number_of_licenses = len(license)
        repository_url = package[9]
        homepage_url = package[10]
        description = package[11]
        
        dependents = []
        for dep in package[12]:
            dependents.append({
                'type': dep[0],
                'name': dep[1],
                'license': dep[2]
            })
        number_of_dependents = len(dependents)
        output.append({
            'purl': purl,
            'type': type,
            'namespace': namespace,
            'name': name,
            'versions': version,
            'qualifiers': qualifiers,
            'subpaths': subpath,
            'licenses': license,
            'number_of_licenses': number_of_licenses,
            'repository_url': repository_url,
            'homepage_url': homepage_url,
            'description': description,
            'dependents': dependents,
            'number_of_dependents': number_of_dependents
        })
    return jsonify(output)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)