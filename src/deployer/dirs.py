import platformdirs


dirs = platformdirs.PlatformDirs("deployer")

clone_path = dirs.user_data_path / "repos"
