from faker import Faker
import random
import os

fake = Faker()

def generate_npm_purl():
    namespace = f"@{fake.word().lower()}" if random.choice([True, False]) else ""
    name = fake.word().lower().replace('_', '-')
    version = f"{fake.random_int(0, 9)}.{fake.random_int(0, 20)}.{fake.random_int(0, 50)}"
    qualifiers = ""
    for _ in range(random.randint(0, 10)):
        key = fake.word().lower()
        value = fake.word().lower()
        qualifiers += f"{key}={value}&"
    qualifiers = qualifiers.rstrip('&')
    subpath = ""
    for _ in range(random.randint(0, 3)):
        subpath += f"/{fake.word().lower()}"
    subpath = subpath.lstrip('/')
    if qualifiers != "":
        qualifiers = "?" + qualifiers
    
    if subpath != "":
        subpath = "#" + subpath
    if namespace:
        return f"pkg:npm/{namespace}/{name}@{version}{qualifiers}{subpath}"
    return f"pkg:npm/{name}@{version}{qualifiers}{subpath}"

def generate_pypi_purl():
    name = fake.word().lower().replace(' ', '-')
    version = f"{fake.random_int(0, 9)}.{fake.random_int(0, 20)}.{fake.random_int(0, 50)}"
    qualifiers = ""
    for _ in range(random.randint(0, 10)):
        key = fake.word().lower()
        value = fake.word().lower()
        qualifiers += f"{key}={value}&"
    qualifiers = qualifiers.rstrip('&')
    subpath = ""
    for _ in range(random.randint(0, 3)):
        subpath += f"/{fake.word().lower()}"
    subpath = subpath.lstrip('/')
    if qualifiers != "":
        qualifiers = "?" + qualifiers
    
    if subpath != "":
        subpath = "#" + subpath
    return f"pkg:pypi/{name}@{version}{qualifiers}{subpath}"

def generate_maven_purl():
    group_id = f"{fake.word().lower()}.{fake.word().lower()}"
    artifact_id = fake.word().lower().replace(' ', '-')
    version = f"{fake.random_int(0, 9)}.{fake.random_int(0, 20)}.{fake.random_int(0, 50)}"
    qualifiers = ""
    for _ in range(random.randint(0, 10)):
        key = fake.word().lower()
        value = fake.word().lower()
        qualifiers += f"{key}={value}&"
    qualifiers = qualifiers.rstrip('&')
    subpath = ""
    for _ in range(random.randint(0, 3)):
        subpath += f"/{fake.word().lower()}"
    subpath = subpath.lstrip('/')
    if qualifiers != "":
        qualifiers = "?" + qualifiers
    
    if subpath != "":
        subpath = "#" + subpath
    return f"pkg:maven/{group_id}/{artifact_id}@{version}{qualifiers}{subpath}"

def generate_docker_purl():
    namespace = fake.word().lower()
    name = fake.word().lower()
    tag = random.choice([f"v{fake.random_int(1, 9)}.{fake.random_int(0, 20)}"])
    qualifiers = ""
    for _ in range(random.randint(0, 10)):
        key = fake.word().lower()
        value = fake.word().lower()
        qualifiers += f"{key}={value}&"
    qualifiers = qualifiers.rstrip('&')
    subpath = ""
    for _ in range(random.randint(0, 3)):
        subpath += f"/{fake.word().lower()}"
    subpath = subpath.lstrip('/')
    if qualifiers != "":
        qualifiers = "?" + qualifiers
    
    if subpath != "":
        subpath = "#" + subpath
    return f"pkg:docker/{namespace}/{name}@{tag}{qualifiers}{subpath}"

def generate_cargo_purl():
    name = fake.word().lower().replace(' ', '_')
    version = f"{fake.random_int(0, 9)}.{fake.random_int(0, 20)}.{fake.random_int(0, 50)}"
    qualifiers = ""
    for _ in range(random.randint(0, 10)):
        key = fake.word().lower()
        value = fake.word().lower()
        qualifiers += f"{key}={value}&"
    qualifiers = qualifiers.rstrip('&')
    subpath = ""
    for _ in range(random.randint(0, 3)):
        subpath += f"/{fake.word().lower()}"
    subpath = subpath.lstrip('/')
    if qualifiers != "":
        qualifiers = "?" + qualifiers
    
    if subpath != "":
        subpath = "#" + subpath
    return f"pkg:cargo/{name}@{version}{qualifiers}{subpath}"

# Mix of different types
generators = [generate_npm_purl, generate_pypi_purl, generate_maven_purl, 
              generate_docker_purl, generate_cargo_purl]

purls = [random.choice(generators)() for _ in range(20000)]

# Save to file
with open('purls.py', 'w') as f:
    f.write("purls = [\n")
    for purl in purls:
        f.write(f"    '{purl}',\n")
    f.write("]\n")

print(f"Generated {len(purls)} purls")
print("\nSamples:")
for purl in purls[:100]:
    print(purl)