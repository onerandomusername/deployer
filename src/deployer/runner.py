import atexit
import builtins
import contextlib
import signal
import subprocess
import sys
import time
from typing import Dict

import dulwich
import dulwich.porcelain
import dulwich.repo
import httpx

from deployer import config, dirs


try:
    import rich.traceback
except ModuleNotFoundError:
    pass
else:

    rich.traceback.install()


SHUTDOWN_TIMEOUT = 3
"Time until the running process is force-killed, in seconds."


def print(*args, **kwargs) -> None:
    """Patch builtins.print to show a logging message."""
    builtins.print("deployer.runner: ", *args, **kwargs)


headers = {"Accept": "application/vnd.github.v3+json"}
if config.GithubAPI.token:
    headers["Authorization"] = "token " + config.GithubAPI.token

ghapi_client = httpx.Client(base_url=str(config.GithubAPI.root), headers=headers)

atexit.register(ghapi_client.close)


def _fetch_ratelimits() -> Dict[str, int]:
    resp = ghapi_client.get("/rate_limit")
    resp.raise_for_status()
    ratelimits = resp.json()["resources"]["core"]
    print(ratelimits)

    return ratelimits


def determine_refresh_rate() -> int:
    """Determinate the refresh rate for pull timing, if not explicitly determined."""
    # since the ratelimit is 60 unauthed requests per hour
    # we will only make requests at a max rate of the limit, capping at 60 * 60 / 20 (every 20 seconds)
    ratelimits = _fetch_ratelimits()

    if ratelimits["remaining"] == 0:
        time.sleep(ratelimits["reset"] - int(time.time()))
        ratelimits = _fetch_ratelimits()

    max_requests_per_hour = min(ratelimits["limit"] / 3, 60 * 60 / 20)

    # seconds in an hour
    seconds_per_hour = 60 * 60
    sleep_delay = seconds_per_hour // max_requests_per_hour
    return sleep_delay


REFRESH_RATE = determine_refresh_rate()

USER, REPO = config.Config.repo.split("/", 1)
REPO_ENDPOINT = f"/repos/{USER}/{REPO}"

DUL_REPO = dulwich.repo.Repo(dirs.clone_path / REPO)


def run(cmd: str) -> None:
    """Run the main loop."""
    # this loop is for testing, once a safe exit is implemented this can be while True
    for _ in range(2):
        proc = subprocess.Popen(cmd.split(), cwd=dirs.clone_path / REPO)

        def kill_at_exit() -> None:
            with contextlib.suppress(Exception):
                proc.kill()

        atexit.register(kill_at_exit)

        #  todo: remove
        time.sleep(2)

        # wait for api here
        # get initial request of newest commit
        resp = ghapi_client.get(REPO_ENDPOINT + "/commits")
        etag = resp.headers["etag"]
        while True:
            headers = {"If-None-Match": etag}
            resp = ghapi_client.get(REPO_ENDPOINT + "/commits", headers=headers)

            if resp.status_code != 304:
                break
            print(f"Sleeping for {REFRESH_RATE}")
            time.sleep(REFRESH_RATE)

        # new process

        print("Sending sigint")
        try:
            proc.send_signal(signal.SIGINT)
        except ProcessLookupError:
            print("process is already dead.")
        else:
            print("Sent sigint.")
        try:
            proc.wait(SHUTDOWN_TIMEOUT)
        except subprocess.TimeoutExpired:
            print("did not quit before shutdown timeout")
            proc.kill()
        print(f"{{=={cmd!r} exited with {proc.returncode}}}")

        # pull
        print("Pulling new commits.")
        dulwich.porcelain.pull(DUL_REPO.path, outstream=sys.stdout.buffer, errstream=sys.stderr.buffer)
        sys.stdout.flush()
        sys.stderr.flush()


0
# restart function


try:

    run(config.Config.command)
except KeyboardInterrupt:
    sys.exit(0)
