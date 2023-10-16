from collections import defaultdict
from typing import Dict, Iterator, List, Type, TypeVar
import json
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

T = TypeVar("T")


class ResultSetIter:
    def __init__(self):
        pass

    def __iter__(self):
        pass

    def __next__(self):
        pass


class ResultSet:
    def __init__(self, value_type=str, xpath=None, sort=False):
        self.results_list = []
        self.results_uniq = defaultdict(list)
        self.value_type = value_type
        self.xpath = xpath
        self.cls = type(self)
        self.cls_name = self.cls.__name__

    def add(self, tag, value, lineno) -> Self:
        if type(value) is not self.value_type:
            raise TypeError(
                f"{value} {type(value)} is not of type {self.value_type}"
            )
        self.results_list.append({"tag": tag, "value": value, "lineno": lineno})
        if self.value_type is str:
            self.results_uniq[value].append(lineno)
        return self

    def all_values(self) -> List[T]:
        return self.results_list

    def append(self, result_set) -> Self:
        if result_set is None:
            raise TypeError(
                f"{type(result_text)} can't be appended to {self.cls_name}"
            )
        for result in result_set.all_values():
            self.results_list.append(result)
            if self.value_type is str:
                self.results_uniq[result["value"]].append(result["lineno"])
        return self

    def first_value(self) -> Dict[str, T]:
        return self.results_list[0]

    def grep(self, filter_func) -> Self:
        filtered = self.cls(value_type=self.value_type)
        for result in result_set.all_values():
            if filter_func(result["value"]):
                filtered.add(result["tag"], result["value"], result["lineno"])
        return filtered if filtered else None

    def isempty(self) -> bool:
        return len(self.results_list) == 0

    def join(self, uniq=True, sep="") -> Self:
        if self.value_type is not str:
            raise TypeError(
                f"{self.cls_name} value type is {self.value_type} but join()"
                " expects str"
            )
        if self.isempty():
            raise ValueError("{self.cls_name} is empty.")

        if uniq:
            values = self.results_uniq.keys()
        else:
            values = [result["value"] for result in self.results_list]

        total_text = ""
        for value in values:
            if total_text:
                total_text += sep
            total_text += value

        joined = self.cls(value_type=self.value_type)
        joined.add(
            self.results_list[0]["tag"],
            total_text.strip(),
            self.results_list[0]["lineno"],
        )
        return joined

    def rs_or_none(self) -> Self:
        return self if self else None

    def string_values(self) -> List[str]:
        if self.value_type is str:
            return list(self.results_uniq.keys())
        else:
            return [
                json.dumps(result["value"], indent=2)
                for result in self.results_list
            ]

    def type(self) -> Type[T]:
        return self.value_type

    def update_values(self, update_func, value_type=None) -> Self:
        if value_type is None:
            value_type = self.value_type
        updated = self.cls(value_type)
        for result in self.all_values():
            updated.add(
                result["tag"], update_func(result["value"]), result["lineno"]
            )
        return updated

    def values(self) -> List[T]:
        if self.value_type is str:
            return list(self.results_uniq.keys())
        else:
            return [result["value"] for result in self.results_list]

    def __bool__(self) -> bool:
        return len(self.results_list) > 0

    def __iter__(self) -> Iterator[T]:
        for result in self.all_values():
            yield result

    def __str__(self) -> str:
        return (
            "\n\n".join(
                [
                    f"({i + 1}) "
                    f"Lineno: {result['lineno']}, "
                    f"Tag: {result['tag']}, "
                    f"Value: '{result['value']}'"
                    for i, result in enumerate(self.results_list)
                ]
            )
            + "\n"
        )
