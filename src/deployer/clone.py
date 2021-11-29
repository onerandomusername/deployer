import dulwich
import dulwich.porcelain
import dulwich.repo

from deployer import config, dirs


clone_path = dirs.clone_path
if not clone_path.exists():
    clone_path.mkdir(parents=True, exist_ok=True)
repo_path = clone_path / config.Config.repo.split("/", 1)[1]
print(repo_path)
if repo_path.exists():
    raise FileExistsError(repo_path)
    pass
else:
    dulwich.porcelain.clone(f"https://github.com/{config.Config.repo}", repo_path)
print(dulwich.porcelain.status(repo_path))

repo = dulwich.repo.Repo(repo_path)

print(repo.head())
