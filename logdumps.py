
from __future__ import annotations

__all__ = ["initialise_log_manager", "create_log_target"]

import os
import sys
import threading
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from io import TextIOWrapper

now = lambda: str(datetime.now()).replace("-", "").replace(":", "").replace(" ", "").replace(".", "")[2:-7:]
md = lambda: f"[{str(datetime.now())[14:19:]}]"
none = lambda: ""

@dataclass(frozen=True)
class LogTarget:
    name: str
    target: TextIOWrapper
    lock: threading.Lock

class LogManager:
    def __init__(self):
        self.logTargets = {}

    def add_file(self, logTarget: LogTarget):
        self.logTargets[logTarget.name] = logTarget

    def add_files(self, logTargets: Sequence[LogTarget]):
        for logTarget in logTargets:
            self.logTargets[logTarget.name] = logTarget

    def get_logs(self) -> list[LogTarget]:
        return list(self.logTargets.values())

    def create_log(self, targets: set[str], timeStamper: Callable[..., str] = md,  defaultKwargs: dict = None) -> Callable[..., None]:
        "given a set of targets from LogManager.logTargets, create_log returns a function that thread-safely"
        "prints to all of those targets."
        default = {
            "flush": True
            }
        use = default | defaultKwargs
        def internal(*args, **kwargs):
            kwargs = use | kwargs
            for logname in self.logTargets:
                if logname in targets:
                    log = self.logTargets[logname]
                    with log.lock:
                        print(timeStamper(), *args, file=log.target, **kwargs)
        return internal 

    def flush(self, target: str):
        self.logTargets[target].target.flush()

    def flush_all(self):
        for target in self.logTargets:
            self.logTargets[target].target.flush()

    def close(self):
        for target in self.logTargets:
            self.logTargets[target].target.close()

STDOUT = LogTarget("stdout", sys.stdout, threading.Lock())
STDERR = LogTarget("stderr", sys.stderr, threading.Lock())

with suppress(OSError):
    os.mkdir("logs")

def initialise_log_manager() -> LogManager:
    LM = LogManager()
    LM.add_files((STDOUT, STDERR))
    return LM

def create_log_target(name: str, route: str) -> LogTarget:
    return LogTarget(name, open(route, "a"), threading.Lock())

if __name__ == "__main__":
    LM = initialise_log_manager()
    LM.add_file(create_log_target("maindebug", "c:/workshop/tools/debug.txt"))
    log = LM.create_log({"stdout", "maindebug"})
    for i in range(100):
        log(i)

