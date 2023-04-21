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

class FileModified():
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

class Handler(FileSystemEventHandler):
    def __init__(self, source: str, target: str, actionLock: threading.Lock, changed:FileModified, addTimeTag=False, largeFileLock=None):
        self.source = source
        self.target = target
        self.fsLock = actionLock
        self.addTimeTag = addTimeTag
        self.changed = changed
        self.observer = Observer()
        self.alive = True
        self.timeout_lock = largeFileLock
        self.timeout_start = datetime.datetime.now()
        
    def start(self):
        self.observer.schedule(self, path=self.source, recursive=True)
        self.observer.start()

    def stop(self):
        self.alive = False
        self.observer.stop()

    def join(self):
        self.observer.join()

    def sameFiles(self, path_a, path_b):
        comp = filecmp.dircmp(a=path_a, b=path_b)
        return (comp.left_only == [] and comp.right_only == [])

    def init_timeout(self):
        if not self.timeout_lock: return
        self.timeout_lock.acquire()
        self.timeout_start = datetime.datetime.now()
        self.timeout_lock.release()

    def on_any_event(self, event):
        if not event.is_directory:
            print(event.event_type)
            if event.event_type == 'moved' or event.event_type == 'created' or event.event_type == "modified":
                self.init_timeout()
                self.fsLock.acquire()
                if not os.path.exists(event.src_path):
                    print(event.src_path + " not found!")
                    self.fsLock.release()
                    return
                file = event.src_path.replace(self.source, "")

                if self.addTimeTag:
                    t = time.localtime()
                    timestamp = time.strftime('%Y-%d-%b_%H%M', t)
                    
                    splitName = file.rsplit(".", 1)
                    file = splitName[0] + "_" + timestamp
                    if len(splitName) > 1:
                        file = file + "." + splitName[1]
                    
                target = self.target + file
                if self.changed and self.addTimeTag:
                    self.changed.modify("mv "+shlex.quote(event.src_path)+" "+ shlex.quote(target))
                elif self.changed:
                    self.changed.modify("cp "+shlex.quote(event.src_path)+" "+ shlex.quote(target))
                self.fsLock.release()
            elif event.event_type == 'deleted':
                self.fsLock.acquire()
                file = event.src_path.replace(self.source, "")
                target = self.target + file
                if os.path.exists(target):
                    if self.changed:
                        self.changed.modify("rm " + shlex.quote(tartet))
                else:
                    print("Target file: "+ target+ " not found!")
                self.fsLock.release()
