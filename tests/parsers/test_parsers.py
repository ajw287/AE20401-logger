import sys
import os

# Add the main directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parsers.data_parser import parse_data_message, message_format

class TestParsers:
    #TODO: Add more tests here!
    test_list = (   ["401:C:0",("401","C","0")],
                    ["401:C:501988010",("401","C","501988010")],
                )

    def test_parse_data_message(self):
        for i, test_command in enumerate(self.test_list):
            result = parse_data_message(test_command[0])
            expected = test_command[1]
            assert len(result) == len(expected)
            for r, e in zip(result, expected):
                assert r == e