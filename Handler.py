import sys
import os
import time
import datetime
from time import sleep
import logging
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import filecmp
import shlex


class FileModified:
    def __init__(self, storeop=False) -> None:
        self.modified = False
        self.operations = []
        self.storeop = storeop

    def modify(self, fileop):
        self.modified = True
        if self.storeop:
            if fileop not in self.operations:
                print(fileop + " : will be executed on replug!")
                self.operations.append(fileop)
        else:
            os.system(fileop)
            print(fileop + " executed!")


def sameFiles(path_a, path_b):
    comp = filecmp.dircmp(path_a, path_b)
    return comp.left_only == [] and comp.right_only == []


class Handler(FileSystemEventHandler):
    def __init__(self, source: str, target: str, actionLock: threading.Lock, changed: FileModified, addTimeTag=False,
                 largeFileLock=None):
        self.source = source
        self.target = target
        self.fsLock = actionLock
        self.changed = changed
        self.observer = Observer()
        self.alive = True
        self.timeout_start = datetime.datetime.now()

    def start(self):
        self.observer.schedule(self, path=self.source, recursive=True)
        self.observer.start()

    def stop(self):
        self.alive = False
        self.observer.stop()

    def join(self):
        self.observer.join()

    def init_timeout(self):
        if not self.fsLock:
            return
        print("received data ...")
        self.fsLock.acquire()
        self.timeout_start = datetime.datetime.now()
        self.fsLock.release()

    def handle_file(self, src_path):
        print(f"Received {src_path}")
        self.fsLock.acquire()
        for file in os.listdir(self.target):
            if os.path.join(self.target, file) != src_path:
                path = os.path.join(self.target, file.replace(" ", "\ "))
                print(f"moving: {path} to {self.source}")
                os.system(f"mv {path} {self.source}")

        print("waiting for timeout")
        timeout_after = 5
        while (
            time_delta := (datetime.datetime.now() - self.timeout_start).total_seconds()
        ) < timeout_after:
            print(f"last package {time_delta}s ago")
            self.fsLock.release()
            sleep(timeout_after - time_delta)
            self.fsLock.acquire()
        if os.path.exists(".update"):
            os.remove(".update")
        if not os.path.exists(".update_static"):
            open(".update_static", "w")
        if os.path.exists("update.sh"):
            os.system("bash update.sh")
        self.fsLock.release()
        sleep(30)  # TODO: clear waiting thread queue for large files
        self.fsLock.acquire()
        self.received.remove(src_path)
        self.fsLock.release()

    def on_any_event(self, event):
        if not event.is_directory:
            print(event.event_type)
            if (
                event.event_type == "moved"
                or event.event_type == "created"
                or event.event_type == "modified"
                and self.target in event.src_path
            ):
                self.init_timeout()
                if event.event_type == "created":
                    self.fsLock.acquire()
                    if event.src_path in self.received:
                        return self.fsLock.release()
                    self.received.append(event.src_path)
                    self.fsLock.release()
                    thrd = threading.Thread(
                        target=self.handle_file, args=(str(event.src_path),)
                    )
                    thrd.start()

                if self.addTimeTag:
                    t = time.localtime()
                    timestamp = time.strftime('%Y-%d-%b_%H%M', t)

                    splitName = file.rsplit(".", 1)
                    file = splitName[0] + "_" + timestamp
                    if len(splitName) > 1:
                        file = file + "." + splitName[1]
                if self.target:
                    target = self.target + file
                    if self.changed and self.addTimeTag:
                        self.changed.modify("mv " + shlex.quote(event.src_path) + " " + shlex.quote(target))
                    elif self.changed:
                        self.changed.modify("cp " + shlex.quote(event.src_path) + " " + shlex.quote(target))
                self.fsLock.release()
            elif event.event_type == 'deleted':
                self.fsLock.acquire()
                file = event.src_path.replace(self.source, "")
                if self.target:
                    target = self.target + file
                    if os.path.exists(target):
                        if self.changed:
                            self.changed.modify("rm " + shlex.quote(target))
                    else:
                        print("Target file: " + target + " not found!")
                self.fsLock.release()
