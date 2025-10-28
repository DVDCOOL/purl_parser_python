from faker import Faker
import random
import os

class PurlGenerator:
    def __init__(self):
        self.fake = Faker()

    def generate_npm_purl(self):
        namespace = f"@{self.fake.word().lower()}" if random.choice([True, False]) else ""
        name = self.fake.word().lower().replace('_', '-')
        version = f"{self.fake.random_int(0, 9)}.{self.fake.random_int(0, 20)}.{self.fake.random_int(0, 50)}"
        qualifiers = ""
        for _ in range(random.randint(0, 10)):
            key = self.fake.word().lower()
            value = self.fake.word().lower()
            qualifiers += f"{key}={value}&"
        qualifiers = qualifiers.rstrip('&')
        subpath = ""
        for _ in range(random.randint(0, 3)):
            subpath += f"/{self.fake.word().lower()}"
        subpath = subpath.lstrip('/')
        if qualifiers != "":
            qualifiers = "?" + qualifiers
        
        if subpath != "":
            subpath = "#" + subpath
        if namespace:
            return f"pkg:npm/{namespace}/{name}@{version}{qualifiers}{subpath}"
        return f"pkg:npm/{name}@{version}{qualifiers}{subpath}"

    def generate_pypi_purl(self):
        name = self.fake.word().lower().replace(' ', '-')
        version = f"{self.fake.random_int(0, 9)}.{self.fake.random_int(0, 20)}.{self.fake.random_int(0, 50)}"
        qualifiers = ""
        for _ in range(random.randint(0, 10)):
            key = self.fake.word().lower()
            value = self.fake.word().lower()
            qualifiers += f"{key}={value}&"
        qualifiers = qualifiers.rstrip('&')
        subpath = ""
        for _ in range(random.randint(0, 3)):
            subpath += f"/{self.fake.word().lower()}"
        subpath = subpath.lstrip('/')
        if qualifiers != "":
            qualifiers = "?" + qualifiers
        
        if subpath != "":
            subpath = "#" + subpath
        return f"pkg:pypi/{name}@{version}{qualifiers}{subpath}"

    def generate_maven_purl(self):
        group_id = f"{self.fake.word().lower()}.{self.fake.word().lower()}"
        artifact_id = self.fake.word().lower().replace(' ', '-')
        version = f"{self.fake.random_int(0, 9)}.{self.fake.random_int(0, 20)}.{self.fake.random_int(0, 50)}"
        qualifiers = ""
        for _ in range(random.randint(0, 10)):
            key = self.fake.word().lower()
            value = self.fake.word().lower()
            qualifiers += f"{key}={value}&"
        qualifiers = qualifiers.rstrip('&')
        subpath = ""
        for _ in range(random.randint(0, 3)):
            subpath += f"/{self.fake.word().lower()}"
        subpath = subpath.lstrip('/')
        if qualifiers != "":
            qualifiers = "?" + qualifiers
        
        if subpath != "":
            subpath = "#" + subpath
        return f"pkg:maven/{group_id}/{artifact_id}@{version}{qualifiers}{subpath}"

    def generate_docker_purl(self):
        namespace = self.fake.word().lower()
        name = self.fake.word().lower()
        tag = random.choice([f"v{self.fake.random_int(1, 9)}.{self.fake.random_int(0, 20)}"])
        qualifiers = ""
        for _ in range(random.randint(0, 10)):
            key = self.fake.word().lower()
            value = self.fake.word().lower()
            qualifiers += f"{key}={value}&"
        qualifiers = qualifiers.rstrip('&')
        subpath = ""
        for _ in range(random.randint(0, 3)):
            subpath += f"/{self.fake.word().lower()}"
        subpath = subpath.lstrip('/')
        if qualifiers != "":
            qualifiers = "?" + qualifiers
        
        if subpath != "":
            subpath = "#" + subpath
        return f"pkg:docker/{namespace}/{name}@{tag}{qualifiers}{subpath}"

    def generate_cargo_purl(self):
        name = self.fake.word().lower().replace(' ', '_')
        version = f"{self.fake.random_int(0, 9)}.{self.fake.random_int(0, 20)}.{self.fake.random_int(0, 50)}"
        qualifiers = ""
        for _ in range(random.randint(0, 10)):
            key = self.fake.word().lower()
            value = self.fake.word().lower()
            qualifiers += f"{key}={value}&"
        qualifiers = qualifiers.rstrip('&')
        subpath = ""
        for _ in range(random.randint(0, 3)):
            subpath += f"/{self.fake.word().lower()}"
        subpath = subpath.lstrip('/')
        if qualifiers != "":
            qualifiers = "?" + qualifiers
        
        if subpath != "":
            subpath = "#" + subpath
        return f"pkg:cargo/{name}@{version}{qualifiers}{subpath}"

def generate_fake_purls():
    faker = PurlGenerator()

    # Mix of different types
    generators = [faker.generate_npm_purl, faker.generate_pypi_purl, faker.generate_maven_purl, 
                faker.generate_docker_purl, faker.generate_cargo_purl]

    purls = [random.choice(generators)() for _ in range(20000)]

    # Save to file
    with open('purl_parserproject/purls.py', 'w') as f:
        f.write("purls = [\n")
        for purl in purls:
            f.write(f"    '{purl}',\n")
        f.write("]\n")

    print(f"Generated {len(purls)} purls")

    return purls
        
if __name__ == "__main__":
    purls = generate_fake_purls()
    print("\nSamples:")
    for purl in purls[:100]:
        print(purl)