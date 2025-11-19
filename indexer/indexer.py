import sys
import os
from database.functionsForDB import Database
from database.visualizeDB import DependencyAnalytics
import sys
import redis
import json

DB_PATH = os.getenv('DB_PATH', './shared/database/packages.db')
TIMEOUT = int(os.getenv('TIMEOUT', '60'))

class DependencyIntegrator:
    """Integrates DependentFinder with Database to store packages and dependencies"""
    
    def __init__(self, db_path, prints=False):
        self.db = Database(db_path)
        self.prints = prints
        redis_host = os.getenv('REDIS_HOST', 'localhost')  # Get from environment
        self.queue = redis.Redis(host=redis_host, port=6379, db=0, password=os.getenv('REDIS_PASSWORD', None))
        self.queue.delete('processed_packages')
        self.timeout = TIMEOUT #seconds
        self.addAllPackagesToCache()

    def addAllPackagesToCache(self):
        """Preload all packages from DB into cache to minimize DB queries"""
        
        
        all_packages = self.db.getAllPackages()
        for pkg in all_packages:
            self.queue.sadd('processed_packages', f"{pkg[2]}/{pkg[4]}")

        print(f"Loaded {len(all_packages)} packages into cache.")
        self.queue.sadd('processed_packages', 'true')

    def storeDependenciesFromFinder(self):

        while True:
            message = self.queue.brpop('work_queue')
            if message:
                data = json.loads(message[1])
                if data.get('type') == 'package':
                    ecosystem = data['ecosystem']
                    name = data['name']
                    license = data['license']
                    description = data['description']
                    purl = data['purl']
                    repository_url = data['repository_url']
                    homepage_url = data['homepage']
                    version = data['version']
                    normalized_license = data['normalized_license']
                    try:
                        success, packageIDs = self.db.insertPackageWithLicense(
                            type=ecosystem,
                            namespace=None,
                            name=name,
                            version=version,
                            qualifiers=None,
                            subpath=None,
                            license=license,
                            description=description,
                            purl=purl,
                            repository_url=repository_url,
                            homepage_url=homepage_url,
                            normalized_license=normalized_license
                        )
                        
                        if success and packageIDs:
                            print(f"Inserted package: {ecosystem}/{name} with ID {packageIDs[0]}")
                            self.queue.sadd('processed_packages', f"{ecosystem}/{name}")
                            
                        elif packageIDs:
                            if self.prints:
                                print(f"Package already exists: {ecosystem}/{name} with ID {packageIDs[0]}")
                            self.queue.sadd('processed_packages', f"{ecosystem}/{name}")
                        else:
                            if self.prints:
                                print(f"Skipped package: {ecosystem}/{name}")
                            
                    except Exception as e:
                        print(f"Error inserting package {ecosystem}/{name}: {str(e)}")
                elif data.get('type') == 'relation':
                    parent_info = data['parent']
                    child_info = data['child']
                    parent_ecosystem = parent_info['ecosystem']
                    parent_name = parent_info['name']
                    child_ecosystem = child_info['ecosystem']
                    child_name = child_info['name']

                    try:
                        parent_id = self.db.getPackageID(parent_ecosystem, parent_name)
                        child_id = self.db.getPackageID(child_ecosystem, child_name)

                        if parent_id and child_id:
                            success = self.db.insertDependency(
                                packageID=child_id,
                                dependsOnPackageID=parent_id,
                            )
                            
                            if success and self.prints:
                                print(f"Inserted dependency: {child_name} depends on {parent_name}")
                            else:
                                if self.prints:
                                    print(f"Dependency already exists: {child_name} depends on {parent_name}")
                        else:
                            if self.prints:
                                print(f"Missing PackageID for dependency: {child_name} -> {parent_name}")
                            
                    except Exception as e:
                        print(f"Error inserting dependency {child_name} -> {parent_name}: {str(e)}")
            else:
                print("No more messages in queue. Exiting.")
                x = self.db.getAllPackages()
                break
    def close(self):
        """Close database connection"""
        self.db.close()

# ========== MAIN EXECUTION SCRIPT ==========

def main():
    # Configuration
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return
    integrator = DependencyIntegrator(DB_PATH)
    integrator.storeDependenciesFromFinder()
    integrator.close()
    analytics = DependencyAnalytics(DB_PATH)
    analytics.generateHTMLReport()
    analytics.close()

if __name__ == "__main__":

    main()
