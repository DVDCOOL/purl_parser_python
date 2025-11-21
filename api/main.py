from flask import Flask, jsonify, request
from database.functionsForDB import Database
import os

DB_PATH = os.getenv('DB_PATH', './shared/database/packages.db')

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'PURL Parser API is running'}), 200

@app.route('/get_number_of_packages', methods=['GET'])
def get_number_of_packages():
    if not os.path.exists(DB_PATH):
        message = f"Database file not found at {DB_PATH}"
        return jsonify({'message': message}), 503
    db = Database(DB_PATH)
    count = len(db.getAllPackages())
    db.close()
    return jsonify({'number_of_packages': count}), 200

@app.route('/get_packages', methods=['GET'])
def get_packages():
    #Get optional query parameters for pagination
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=100, type=int)
    per_page = min(per_page, 100)  # Limit maximum per_page to 100

    if not os.path.exists(DB_PATH):
        message = f"Database file not found at {DB_PATH}"
        return jsonify({'message': message}), 503
    db = Database(DB_PATH)
    packages = db.getAllPackages()[per_page*(page-1):per_page*page]
    output = []
    if len (packages) > 0:
        for package in packages:
            purl = package[1]
            ecosystem = package[2]
            namespace = package[3]
            name = package[4]
            version = [{'version': i} for i in (package[5] or [])]
            qualifiers = [{'key': q[0], 'value': q[1]} for q in (package[6] or [])]
            subpath = [{'subpath': i} for i in (package[7] or [])]
            license = [{'license': i} for i in (package[8] or [])]
            number_of_licenses = len(license)
            repository_url = package[9]
            homepage_url = package[10]
            description = package[11]
            dependents = [{'ecosystem': dep[0], 'name': dep[1], 'license': dep[2]} for dep in (package[12] or [])]
            number_of_dependents = len(dependents)
            output.append({
                'purl': purl,
                'ecosystem': ecosystem,
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
    db.close()
    return jsonify({'packages': output}), 200

@app.route('/insert_package/', methods=['POST'])
def insert_package():
    data = request.get_json()
    if not os.path.exists(DB_PATH):
        message = f"Database file not found at {DB_PATH}"
        return jsonify({'message': message}), 503
    db = Database(DB_PATH)

    # Extract package information from the request data
    ecosystem = data.get('ecosystem')
    namespace = data.get('namespace', None)
    name = data.get('name')
    version = data.get('version')
    qualifiers = data.get('qualifiers', None)
    subpath = data.get('subpath', None)
    license = data.get('license', None)
    repository_url = data.get('repository_url')
    homepage_url = data.get('homepage_url')
    description = data.get('description')
    normalized_license = data.get('normalized_license', None)
    try:
        # Insert the package into the database
        success, package_ids = db.insertPackageWithLicense(
            ecosystem=ecosystem,
            namespace=namespace,
            name=name,
            version=version,
            qualifiers=qualifiers,
            subpath=subpath,
            license=license,
            repository_url=repository_url,
            homepage_url=homepage_url,
            description=description,
            normalized_license=normalized_license
        )
        db.close()
        if success:
            return jsonify({'message': f"Inserted package: {ecosystem}/{name} with ID {package_ids[0]}", 'package_ids': package_ids}), 201
        else:
            if package_ids:
                return jsonify({'message': f"Package already exists: {ecosystem}/{name}", 'package_ids': package_ids}), 400
            return jsonify({'message': f"Failed to insert package: {ecosystem}/{name}"}), 400
    except Exception as e:
        return jsonify({'message': f"Error inserting package {ecosystem}/{name}: {str(e)}"}), 500
    
@app.route('/insert_relation/', methods=['POST'])
def insert_relation():
    data = request.get_json()
    if not os.path.exists(DB_PATH):
        return jsonify({'message': f"Database file not found at {DB_PATH}"}), 503
    db = Database(DB_PATH)

    parent_info = data['parent']
    child_info = data['child']
    parent_ecosystem = parent_info['ecosystem']
    parent_name = parent_info['name']
    child_ecosystem = child_info['ecosystem']
    child_name = child_info['name']

    try:
        parent_id = db.getPackageID(parent_ecosystem, parent_name)
        child_id = db.getPackageID(child_ecosystem, child_name)

        if parent_id and child_id:
            success = db.insertDependency(
                packageID=child_id,
                dependsOnPackageID=parent_id,
            )
            db.close()
            if success:
                message = f"Inserted dependency: {child_name} depends on {parent_name}"
                return jsonify({'message': message}), 201
            else:
                message = f"Dependency already exists: {child_name} -> {parent_name}"
                return jsonify({'message': message}), 400
        else:
            message = f"Failed to insert dependency: {child_name} -> {parent_name}"
            return jsonify({'message': message}), 400

    except Exception as e:
        message = f"Error inserting dependency {child_name} -> {parent_name}: {str(e)}"
        return jsonify({'message': message}), 500

    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)