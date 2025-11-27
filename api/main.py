from flask import Flask, jsonify, request
from database.functionsForDB import Database
import os
from threading import Lock
from functools import wraps

DB_PATH = os.getenv('DB_PATH', './shared/database/packages.db')

app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')

# Write lock for DuckDB - reads can be concurrent, writes must be serialized
write_lock = Lock()

def with_db_read(f):
    """Decorator for read operations - uses read-only connection"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not os.path.exists(DB_PATH):
            return jsonify({'message': f"Database file not found at {DB_PATH}"}), 503
        
        db = Database(DB_PATH, read_only=True)
        try:
            result = f(db, *args, **kwargs)
            return result
        finally:
            db.close()
    
    return decorated_function

def with_db_write(f):
    """Decorator for write operations - serialized with lock"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not os.path.exists(DB_PATH):
            return jsonify({'message': f"Database file not found at {DB_PATH}"}), 503
        
        with write_lock:
            db = Database(DB_PATH, read_only=False)
            try:
                result = f(db, *args, **kwargs)
                return result
            finally:
                db.close()
    
    return decorated_function


@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'PURL Parser API is running'}), 200


@app.route('/get_number_of_packages', methods=['GET'])
@with_db_read
def get_number_of_packages(db):
    """Use optimized COUNT query"""
    count = db.getPackageCount()
    return jsonify({'number_of_packages': count}), 200


@app.route('/get_packages', methods=['GET'])
@with_db_read
def get_packages(db):
    """Use native DuckDB pagination - concurrent reads work great!"""
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=100, type=int)
    per_page = min(per_page, 100)
    
    if page < 1:
        return jsonify({'message': 'Page must be >= 1'}), 400
    
    offset = per_page * (page - 1)
    
    # Use optimized pagination
    packages = db.getPackagesPaginated(limit=per_page, offset=offset)
    
    output = []
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
        dependents = [{'ecosystem': dep[0], 'name': dep[2], 'license': dep[4]} 
                     for dep in (package[12] or [])]
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
    
    # Calculate if there's a next page
    total_packages = db.getPackageCount()
    has_next = (offset + per_page) < total_packages
    
    return jsonify({
        'packages': output,
        'page': page,
        'limit': per_page,
        'has_next': has_next,
        'total_packages': total_packages
    }), 200


@app.route('/insert_package/', methods=['POST'])
@with_db_write
def insert_package(db):
    """Write operation - serialized"""
    data = request.get_json()
    
    if not data.get('ecosystem') or not data.get('name'):
        return jsonify({'message': 'Missing required fields: ecosystem, name'}), 400
    
    try:
        success, package_ids = db.insertPackageWithLicense(
            ecosystem=data.get('ecosystem'),
            namespace=data.get('namespace'),
            name=data.get('name'),
            version=data.get('version'),
            qualifiers=data.get('qualifiers'),
            subpath=data.get('subpath'),
            license=data.get('license'),
            purl=data.get('purl'),
            repository_url=data.get('repository_url'),
            homepage_url=data.get('homepage_url'),
            description=data.get('description'),
            normalized_license=data.get('normalized_license')
        )
        
        if success:
            return jsonify({
                'message': f"Inserted package: {data.get('ecosystem')}/{data.get('name')}", 
                'package_ids': package_ids
            }), 201
        else:
            if package_ids:
                return jsonify({
                    'message': f"Package already exists: {data.get('ecosystem')}/{data.get('name')}", 
                    'package_ids': package_ids
                }), 200
            return jsonify({'message': f"Failed to insert package"}), 400
            
    except Exception as e:
        app.logger.error(f"Error inserting package: {str(e)}")
        return jsonify({'message': f"Error inserting package: {str(e)}"}), 500


@app.route('/insert_relation/', methods=['POST'])
@with_db_write
def insert_relation(db):
    """Write operation - serialized"""
    data = request.get_json()
    
    if not data.get('parent') or not data.get('child'):
        return jsonify({'message': 'Missing required fields: parent, child'}), 400
    
    parent_info = data['parent']
    child_info = data['child']
    
    parent_ecosystem = parent_info.get('ecosystem')
    parent_name = parent_info.get('name')
    child_ecosystem = child_info.get('ecosystem')
    child_name = child_info.get('name')
    
    if not all([parent_ecosystem, parent_name, child_ecosystem, child_name]):
        return jsonify({'message': 'Incomplete parent or child information'}), 400
    
    try:
        parent_id = db.getPackageID(parent_ecosystem, parent_name)
        child_id = db.getPackageID(child_ecosystem, child_name)
        
        if not parent_id:
            return jsonify({'message': f"Parent package not found: {parent_ecosystem}/{parent_name}"}), 404
        
        if not child_id:
            return jsonify({'message': f"Child package not found: {child_ecosystem}/{child_name}"}), 404
        
        success = db.insertDependency(
            packageID=child_id,
            dependsOnPackageID=parent_id,
        )
        
        if success:
            return jsonify({'message': f"Inserted dependency: {child_name} depends on {parent_name}"}), 201
        else:
            return jsonify({'message': f"Dependency already exists: {child_name} -> {parent_name}"}), 200
            
    except Exception as e:
        app.logger.error(f"Error inserting dependency: {str(e)}")
        return jsonify({'message': f"Error inserting dependency: {str(e)}"}), 500


if __name__ == '__main__':
    # DuckDB handles concurrent reads well!
    app.run(
        host='0.0.0.0', 
        port=int(os.getenv('API_PORT', '8080')), 
        debug=True,
        threaded=True  # Enable threading for concurrent requests
    )