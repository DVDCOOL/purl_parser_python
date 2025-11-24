import sys
import os
from purl_parserproject.purl_parser import PurlParser
import requests
import json
import time
import redis
import signal
import atexit
import threading

NUMBER_OF_LEVELS = int(os.getenv('NUMBER_OF_LEVELS', '5'))
HEADERS = json.loads(os.getenv('HEADERS', None) or '{}')
TIMEOUT = int(os.getenv('TIMEOUT', '60'))
LOCK_TTL_SECONDS = int(os.getenv('LOCK_TTL_SECONDS', '600'))

class DependentFinder:
    def __init__(self, prints=False):
        self.prints = prints
        self.requestRemaining = None
        self.requestLimit = 0
        self.start_time = time.time()
        self.requestMade = 0
        self.packages = []
        self.timeout = TIMEOUT
        self.failed = False
        self.shutdown_requested = False
        self.current_locks = []
        self._cleanup_lock = threading.Lock()
        self._cleanup_done = False

        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_password = os.getenv('REDIS_PASSWORD')
        if redis_password == '':
            redis_password = None
            
        self.queue = redis.Redis(
            host=redis_host, 
            port=os.getenv('REDIS_PORT', 6379),
            db=0, 
            password=redis_password,
            decode_responses=True
        )
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Register cleanup on ANY exit (backup)
        atexit.register(self._cleanup_on_exit)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_name = signal.Signals(signum).name
        print(f"\n⚠️  Received signal {signum} ({signal_name}). Initiating graceful shutdown...")
        self.shutdown_requested = True
        self._release_all_locks()

    def _cleanup_on_exit(self):
        """Backup cleanup - runs on any exit"""
        if not self._cleanup_done and self.current_locks:
            print("🧹 atexit: Final cleanup...")
            self._release_all_locks()

    def _release_all_locks(self):
        """Release all locks held by this instance (thread-safe, idempotent)"""
        with self._cleanup_lock:
            if self._cleanup_done:
                if self.prints:
                    print("   (Cleanup already done, skipping)")
                return
            
            if not self.current_locks:
                if self.prints:
                    print("   (No locks to release)")
                self._cleanup_done = True
                return
            
            print(f"🔓 Releasing {len(self.current_locks)} locks...")
            
            locks_to_release = list(self.current_locks)
            self.current_locks.clear()
            
            for lock_key in locks_to_release:
                try:
                    self.queue.delete(lock_key)
                    if self.prints:
                        print(f"   Released: {lock_key}")
                except Exception as e:
                    print(f"   ⚠️  Failed to delete Redis key {lock_key}: {e}")
            
            self._cleanup_done = True
            print(f"✅ Successfully released {len(locks_to_release)} locks")

    def cleanup_stale_locks(self):
        """
        STARTUP CLEANUP: Remove stale locks from previous crashes
        Safe for multi-worker: Only removes locks older than TTL
        """
        print("🧹 Checking for stale locks from previous crashes...")
        
        lock_keys = self.queue.keys("processing_lock:*")
        
        if not lock_keys:
            print("   No locks found.")
            return
        
        cleaned = 0
        for lock_key in lock_keys:
            ttl = self.queue.ttl(lock_key)
            
            if ttl == -1:
                self.queue.delete(lock_key)
                cleaned += 1
                print(f"   🗑️  Removed stale lock: {lock_key} (no TTL)")
            elif ttl == -2:
                continue
            elif ttl < 60:
                self.queue.delete(lock_key)
                cleaned += 1
                print(f"   🗑️  Removed expiring lock: {lock_key} (TTL: {ttl}s)")
        
        if cleaned > 0:
            print(f"✅ Cleaned {cleaned} stale locks")
        else:
            print("✅ No stale locks found")

    def checkWaitingRoom(self):
        """Check if there are packages in the waiting room"""
        self.cleanup_stale_locks()
        
        while self.queue.lpos('waiting_room', 'true') is None:
            if self.shutdown_requested:
                return
            print("Waiting room wasn't ready yet. Sleeping for 10 seconds...")
            time.sleep(10)
        
        while True:
            if self.shutdown_requested:
                return
                
            message = self.queue.brpop('waiting_room', timeout=self.timeout)
            if message is None:
                print("No more packages in waiting room. Checking processing queue.")
                break
            
            purl = message[1]
            if purl != 'true':
                parsedPurl = PurlParser(purl)
                if parsedPurl.validPurl:
                    self.queue.lpush('processing_purl', purl)
                    self.findFirstPackage(parsedPurl)
                    self.queue.lrem('processing_purl', 0, purl)
                    print(f"Finished processing PURL: {purl}")
                else:
                    print(f"Invalid PURL: {purl}")

        while True:
            if self.shutdown_requested:
                return
                
            processing_message = self.queue.brpop('processing_purl', timeout=self.timeout)
            if processing_message is None:
                print("No more packages in processing queue. Exiting.")
                break
            purl = processing_message[1]
            parsedPurl = PurlParser(purl)
            if parsedPurl.validPurl:
                self.queue.lpush('processing_purl', purl)
                print(f"Resuming processing PURL from processing queue: {purl}")
                self.findFirstPackage(parsedPurl)
                self.queue.lrem('processing_purl', 0, purl)
                print(f"Finished processing PURL from processing queue: {purl}")
            else:
                print(f"Invalid PURL in processing queue: {purl}")
        print("All done with waiting room and processing queue.")

    def findFirstPackage(self, parsedPurl):
        response = requests.get(
            f"https://packages.ecosyste.ms/api/v1/packages/lookup?ecosystem={parsedPurl.type}&name={parsedPurl.name}",
            headers=HEADERS
        )

        if response.status_code == 200:
            data = response.json()[0]
            self.requestRemaining = int(response.headers.get('x-ratelimit-remaining', 0))
            self.requestLimit = int(response.headers.get('x-ratelimit-limit', 0))
            self.requestMade += 1
            
            if self.prints:
                print(f"Rate limit remaining: {self.requestRemaining}")
            
            while not self.queue.sismember('processed_packages', 'true'):
                if self.shutdown_requested:
                    return
                print("Waiting for cache to load...")
                time.sleep(5)

            print(f"Starting to find dependents for {data.get('name')}...")
            self.findDependents(data)
        else:
            print("Error: Could not fetch package data.")
            print(f"Error: {response.status_code}")
            print(response.text)
            self.requestRemaining = int(response.headers.get('x-ratelimit-remaining', 0))
            print(f"Rate limit remaining: {self.requestRemaining}")
            sys.exit()

    def checkRateLimit(self):
        """Check if we're approaching rate limit and sleep accordingly"""
        if self.shutdown_requested:
            return False
            
        if self.requestRemaining is None:
            return True
        
        if self.requestLimit > 0:
            base_sleep = 3600 / self.requestLimit
            time.sleep(base_sleep)
        
        if self.requestRemaining < self.requestLimit * 0.01:
            print(f"CRITICAL: Only {self.requestRemaining} requests remaining. Stopping for 1 hour.")
            time.sleep(60*60)
            return False
        elif self.requestRemaining < self.requestLimit * 0.05:
            if self.prints:
                print(f"WARNING: Only {self.requestRemaining} requests remaining. Extra delay...")
            time.sleep(2)
        elif self.requestRemaining < self.requestLimit * 0.1:
            if self.prints:
                print(f"CAUTION: {self.requestRemaining} requests remaining.")
            time.sleep(0.5)

        return True

    def updateRateLimit(self, response):
        """Update rate limit from server response"""
        if 'x-ratelimit-remaining' in response.headers:
            self.requestRemaining = int(response.headers.get('x-ratelimit-remaining'))
            
            if self.prints and self.requestLimit > 0:
                progress_interval = max(1, int(self.requestLimit * 0.1))
                if self.requestRemaining % progress_interval == 0: 
                    elapsed_time = (time.time() - self.start_time) / 60
                    print(f"Progress: {self.requestRemaining} requests remaining after {elapsed_time:.1f} minutes")

    def findDependents(self, package, current_level=0, parent_info=None):
        if self.shutdown_requested:
            return
            
        package_name = package.get("name")
        if len(package_name.split('/')) == 2:
            namespace, package_name = package_name.split('/')
        else:
            namespace = None
        license = package.get("licenses")
        ecosystem = package.get("ecosystem")
        purl = package.get("purl")
        repoURL = package.get("repository_url")
        homepageURL = package.get("homepage")
        description = package.get("description")
        version = package.get("latest_release_number")
        normalized_license = package.get("normalized_licenses")
        package_key = f"{ecosystem}/{package_name}"
        
        if current_level >= NUMBER_OF_LEVELS:
            return
        
        if package_key in self.packages:
            return
        
        lock_key = f"processing_lock:{package_key}"
        lock_acquired = False
        
        try:
            lock_acquired = self.queue.set(
                lock_key,
                f"worker_{os.getpid()}_{time.time()}",
                nx=True,
                ex=LOCK_TTL_SECONDS
            )
            
            if not lock_acquired:
                if self.prints:
                    print(f"   ⏭️  Skipping {package_key} (locked by another worker)")
                self.packages.append(package_key)
                return
            
            self.current_locks.append(lock_key)
            
            if self.prints:
                print(f"🔒 Acquired lock: {package_key}")
            
            if not self.queue.sismember('processed_packages', package_key):
                self.queue.lpush('work_queue', json.dumps({
                    'type': 'package',
                    'ecosystem': ecosystem,
                    'namespace': namespace,
                    'name': package_name,
                    'version': version,
                    'qualifiers': None,
                    'subpath': None,
                    'license': license,
                    'purl': purl,
                    'repository_url': repoURL,
                    'homepage': homepageURL,
                    'description': description,
                    'normalized_license': normalized_license
                }))

            self.packages.append(package_key)
            
            if parent_info:
                self.queue.lpush('work_queue', json.dumps({
                    'type': 'relation',
                    'child': {
                        'ecosystem': ecosystem,
                        'name': package_name
                    },
                    'parent': {
                        'ecosystem': parent_info[0],
                        'name': parent_info[1]
                    }
                }))

            dependentsURL = package.get("dependent_packages_url")
            
            if not self.checkRateLimit():
                return
            
            dependents_response = requests.get(dependentsURL + "?latest=true", headers=HEADERS)
            self.requestMade += 1
            self.updateRateLimit(dependents_response)
            
            pages = 1
            
            while dependents_response.status_code == 200:
                if self.shutdown_requested:
                    return
                    
                dependents_data = dependents_response.json()
                
                if not dependents_data:
                    break
                
                last_processed_idx = -1

                for idx, dependent_pkg in enumerate(dependents_data):
                    pkg_key = f"{dependent_pkg.get('ecosystem')}/{dependent_pkg.get('name')}"
                    if self.queue.sismember('processed_packages', pkg_key):
                        last_processed_idx = idx
                    else:
                        break

                if last_processed_idx == len(dependents_data) - 1:
                    last_pkg = dependents_data[-1]
                    last_key = f"{last_pkg.get('ecosystem')}/{last_pkg.get('name')}"
                    if last_key not in self.packages:
                        self.findDependents(dependents_data[-1], current_level + 1, (ecosystem, package_name))
                    
                elif last_processed_idx >= 0:
                    for dependent_idx in range(last_processed_idx, len(dependents_data)):
                        dependent_pkg = dependents_data[dependent_idx]
                        self.queue.xadd(
                            'spider:progress',
                            {
                                'timestamp': time.strftime('%H:%M:%S'),
                                'level': str(current_level),
                                'package': package_name,
                                'dependent_idx': str(dependent_idx + 1),
                                'total_dependents': str(len(dependents_data)),
                                'page': str(pages)
                            },
                            maxlen=1000  # Keep last 1000 entries
                        )
                        self.findDependents(dependent_pkg, current_level + 1, (ecosystem, package_name))
                else:
                    for dependent_idx, dependent_pkg in enumerate(dependents_data):
                        self.queue.xadd(
                            'spider:progress',
                            {
                                'timestamp': time.strftime('%H:%M:%S'),
                                'level': str(current_level),
                                'package': package_name,
                                'dependent_idx': str(dependent_idx + 1),
                                'total_dependents': str(len(dependents_data)),
                                'page': str(pages)
                            },
                            maxlen=1000  # Keep last 1000 entries
                        )
                        self.findDependents(dependent_pkg, current_level + 1, (ecosystem, package_name))
                
                pages += 1
                
                if not self.checkRateLimit():
                    return
                    
                dependents_response = requests.get(dependentsURL + f"?latest=true&page={pages}", headers=HEADERS)
                self.requestMade += 1
                self.updateRateLimit(dependents_response)
                
            if dependents_response.status_code != 200:
                print(f"Error: {dependents_response.status_code}")
        
        except Exception as e:
            print(f"Exception occurred processing {package_key}: {e}")
            self.failed = True
            raise
        
        finally:
            if lock_acquired:
                try:
                    self.queue.delete(lock_key)
                    try:
                        self.current_locks.remove(lock_key)
                    except ValueError:
                        pass
                    
                    if self.prints:
                        print(f"🔓 Released lock: {package_key}")
                except Exception as e:
                    print(f"⚠️  Failed to release lock {lock_key}: {e}")

def main():
    finder = DependentFinder()
    finder.checkWaitingRoom()
    print("Done!!")

if __name__ == "__main__":
    main()