import re
import toml


def get_latest_version():
    with open("CHANGELOG.md", "r") as changelog:
        content = changelog.read()

    # Use regex to find the version numbers
    versions = re.findall(r"## \[(\d+\.\d+\.\d+)\]", content)
    if not versions:
        raise ValueError("No versions found in CHANGELOG.md")

    # Sort versions to find the latest one
    versions.sort(key=lambda s: list(map(int, s.split('.'))))
    return versions[-1]


def update_pyproject_toml(version):
    with open("pyproject.toml", "r") as f:
        pyproject = toml.load(f)

    pyproject['tool']['poetry']['version'] = version

    with open("pyproject.toml", "w") as f:
        toml.dump(pyproject, f)


if __name__ == "__main__":
    latest_version = get_latest_version()
    update_pyproject_toml(latest_version)
    print(f"Updated pyproject.toml to version {latest_version}")
