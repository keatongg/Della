from __future__ import annotations

from datetime import date
from os import PathLike
from os.path import splitext
from os.path import exists

from pathlib import Path

from typing import Any
from typing import TextIO

import toml


class TaskNode:

    _unique_ids: dict[str, Any] = {}
    _current_node: TaskNode
    _root_node: TaskNode

    def __init__(
        self,
        content: str,
        parent: TaskNode | None,
        due_date: date | None = None,
        unique_id: str | None = None,
    ) -> None:
        self.content = content
        self.due_date = due_date
        self.parent = parent

        self._uid: str | None = unique_id

        if parent is not None:
            parent.add_subnode(self)

        else:
            self.is_root = True

        self.subnodes: list[TaskNode] = []

    @classmethod
    def from_dict(cls, init_dict: dict, parent: TaskNode | None = None) -> TaskNode:  # type: ignore

        node_content: str = init_dict["content"]

        node_parent = parent

        node_due_date: date | None = (
            date.fromisoformat(date_str)
            if (date_str := init_dict["due_date"])
            else None
        )

        node_unique_id: str | None = init_dict.get("unique_id")

        new_node = TaskNode(
            content=node_content, parent=node_parent, due_date=node_due_date
        )

        if "subnodes" in init_dict:

            for subdict in init_dict["subnodes"]:
                new_node.add_subnode(TaskNode.from_dict(subdict))

        if node_unique_id is not None:
            if node_unique_id in TaskNode._unique_ids:
                raise KeyError(f"Duplicate ID: {node_unique_id}")

            new_node._uid = node_unique_id
            TaskNode._unique_ids[node_unique_id]

        return new_node

    @classmethod
    def init_from_file(cls, filepath: PathLike | str) -> TaskNode:

        if isinstance(filepath, str):
            filepath = Path(filepath)

        if not exists(filepath):
            raise FileNotFoundError

        _, file_ext = splitext(filepath)

        file_ext: str = file_ext.lower().strip()[1:]

        with open(filepath, "r") as infile:
            data_dict = toml.load(infile)

        loaded_root = cls.from_dict(data_dict)
        TaskNode._root_node = loaded_root
        return loaded_root

    @property
    def unique_id(self):
        return self._uid

    @unique_id.setter
    def unique_id(self, value: str):
        self._uid = value

    @property
    def current_node(self):
        return TaskNode._current_node

    @current_node.setter
    def current_node(self, new_node: TaskNode):
        TaskNode._current_node = new_node

    @property
    def root_node(self):
        return TaskNode._root_node

    @root_node.setter
    def root_node(self, new_node: TaskNode):
        TaskNode._root_node = new_node

    @property
    def full_path(self) -> list[TaskNode]:

        node: TaskNode | None = self

        pathlist: list[TaskNode] = []
        while node is not None:
            pathlist.append(node)
            node = node.parent

        pathlist.reverse()
        return pathlist

    @property
    def full_path_str(self) -> str:
        return "/".join((n.content for n in self.full_path))

    def detatch_from_parent(self):
        if self.parent is not None:
            self.parent.subnodes.remove(self)
            return

        raise AttributeError("Cannot detatch a node with no parents")

    def change_parent(self, new_parent: TaskNode):
        if self in new_parent.subnodes:
            raise AttributeError(
                "This node is already a subnode of the specified parent node"
            )

        self.detatch_from_parent()
        self.parent = new_parent
        self.parent.add_subnode(self)

    def add_subnode(self, new_node: TaskNode):
        self.subnodes.append(new_node)

    def change_date(self, new_date: date):
        self.due_date = new_date

    def to_dict(self, depth: int = -1) -> dict[str, Any]:

        node_dict: dict[str, str | list[dict]] = {
            "parent": self.parent.content if self.parent is not None else "",
            "content": self.content,
            "due_date": self.due_date.isoformat() if self.due_date is not None else "",
        }

        if self._uid is not None:
            node_dict["unique_id"] = self._uid

        if depth != 0 and self.subnodes:

            node_dict["subnodes"] = [c.to_dict(depth=depth - 1) for c in self.subnodes]

        return node_dict

    def serialize(self, fstream: TextIO) -> str:

        if not fstream.writable():
            raise IOError("Cannot write to stream")

        return toml.dump(self.to_dict(depth=-1), fstream)

    def __iter__(self):
        return ((n) for n in self.subnodes)

    def __str__(self) -> str:  # type: ignore
        date_str = (
            f" [{self.due_date.isoformat()}]" if self.due_date is not None else ""
        )
        return self.content + date_str

    def display(self, depth: int = 0):
        pass
